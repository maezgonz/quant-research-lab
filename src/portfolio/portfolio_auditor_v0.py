# =====================================================================
# 0. LIBRERIAS E IMPORTACIONES
# =====================================================================
import sys
import traceback
import warnings
import webbrowser
from pathlib import Path

# Forzar UTF-8 en consola: QuantStats imprime caracteres como '﹪' (U+FE6A)
# que la codificación cp1252 de Windows no soporta (UnicodeEncodeError).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import quantstats as qs  # quantstats-pro v0.4.5 (drop-in replacement)
import requests
import urllib3
import yfinance as yf
from tqdm import tqdm

# ingnorar los warnings
warnings.filterwarnings("ignore")

# Desactivar advertencias de seguridad para sitios .gob.ar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# 1. DEFINICIÓN DEL PORTFOLIO REAL
# =====================================================================
PORTFOLIO = [
    # STOCKS (Panel Líder y General)
    {"ticker": "PAMP", "cant": 999, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "EDN", "cant": 1378, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "TGSU2", "cant": 646, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "TGNO4", "cant": 837, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "YPFD", "cant": 111, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "METR", "cant": 2545, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "GGAL", "cant": 558, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "BMA", "cant": 68, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "TRAN", "cant": 182, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "MOLI", "cant": 63, "start": "2023-10-09", "tipo": "stocks"},
    {"ticker": "MORI", "cant": 26867, "start": "2023-10-09", "tipo": "stocks"},
    # BONDS (Soberanos)
    {"ticker": "AE38", "cant": 3191, "start": "2026-01-30", "tipo": "bonds"},
    {"ticker": "AL41", "cant": 4069, "start": "2023-10-09", "tipo": "bonds"},
    {"ticker": "GD41", "cant": 885, "start": "2023-10-09", "tipo": "bonds"},
    {"ticker": "AL30", "cant": 6019, "start": "2023-10-09", "tipo": "bonds"},
    {"ticker": "GD30", "cant": 6403, "start": "2023-10-09", "tipo": "bonds"},
    # BOPREAL (Hardcoded Entry Px $749,1373)
    {
        "ticker": "BPOA7",
        "cant": 872,
        "start": "2024-04-01",
        "tipo": "bonds",
        "entry_px": 749.1373,
    },
    {
        "ticker": "BPOB7",
        "cant": 883,
        "start": "2024-04-01",
        "tipo": "bonds",
        "entry_px": 749.1373,
    },
    {
        "ticker": "BPOC7",
        "cant": 1308,
        "start": "2024-04-01",
        "tipo": "bonds",
        "entry_px": 749.1373,
    },
    {
        "ticker": "BPOD7",
        "cant": 1327,
        "start": "2024-04-01",
        "tipo": "bonds",
        "entry_px": 749.1373,
    },
    # NOTES (Lecaps)
    {"ticker": "S30N6", "cant": 92539332, "start": "2026-08-12", "tipo": "notes"},
]

# --- LÓGICA DE FECHA MÍNIMA ---
oldest_purchase = min([pd.to_datetime(asset["start"]) for asset in PORTFOLIO])
start_str = oldest_purchase.strftime("%Y-%m-%d")


# =====================================================================
# 2. FETCHING DE DATOS (HÍBRIDO DATA912 + YFINANCE)
# =====================================================================
# BYMA cotiza bonos y Lecaps cada 100 VN; las acciones por unidad.
PRICE_FACTOR = {"stocks": 1.0, "bonds": 0.01, "notes": 0.01}


def get_data912(ticker, tipo):
    """Serie de cierres diarios (index = fecha normalizada, sin hora/tz)."""
    url = f"https://data912.com/historical/{tipo}/{ticker}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if r.status_code != 200 or not isinstance(data, list) or not data:
            msg = data.get("detail", data) if isinstance(data, dict) else data
            return pd.Series(dtype=float), f"HTTP {r.status_code}: {msg}"
        df = pd.DataFrame(data)
        t_col = "t" if "t" in df.columns else "date"
        idx = pd.to_datetime(df[t_col], unit="s" if t_col == "t" else None)
        if getattr(idx.dt, "tz", None) is not None:
            idx = idx.dt.tz_localize(None)
        s = pd.Series(
            df["c" if "c" in df.columns else "close"].astype(float).values,
            index=idx.dt.normalize(),
        )
        s = s[~s.index.duplicated(keep="last")].sort_index()
        return s[s > 0], None
    except Exception as e:
        return pd.Series(dtype=float), f"{type(e).__name__}: {e}"


print(f"[INFO] Auditoría para {len(PORTFOLIO)} activos...")
prices, units, skipped = {}, {}, []

for asset in tqdm(PORTFOLIO):
    ticker, start = asset["ticker"], pd.to_datetime(asset["start"])
    s, err = get_data912(ticker, asset["tipo"])
    if err:
        skipped.append((ticker, err))
        continue

    s = s[s.index >= start].copy()

    # Precio de entrada real (ej. Bopreales): se fija en la fecha de compra
    # para que el primer retorno sea entry_px -> primer cierre de mercado.
    if "entry_px" in asset:
        s.loc[start] = asset["entry_px"]
        s = s.sort_index()

    if len(s) < 2:
        skipped.append((ticker, f"sin suficientes precios desde {asset['start']}"))
        continue

    prices[ticker] = s
    units[ticker] = asset["cant"] * PRICE_FACTOR[asset["tipo"]]

if skipped:
    print(f"\n[WARN] {len(skipped)} activo(s) EXCLUIDOS del cálculo (sin histórico):")
    for t, why in skipped:
        print(f"       - {t}: {why}")

if not prices:
    raise SystemExit("[ERROR] Ningún activo tiene histórico; no se puede auditar.")

# --- RETORNOS TIME-WEIGHTED (neutros a aportes de capital) ---
px = pd.DataFrame(prices).sort_index()
held = px.notna().cumsum() > 0  # True desde la compra en adelante
px = px.ffill().where(held)  # días sin cotización = último precio, no 0

values = px * pd.Series(units)  # valor de cada posición en ARS
asset_rets = px.pct_change(fill_method=None)

# Peso de cada activo = valor al cierre anterior. Un activo recién comprado
# no tiene valor previo, así que su "entrada" no se computa como retorno.
w_prev = values.shift(1).where(asset_rets.notna())
strategy_rets = (
    (w_prev * asset_rets).sum(axis=1, min_count=1) / w_prev.sum(axis=1, min_count=1)
).dropna()

# Comparación con el método anterior (pct_change del valor total)
naive_rets = values.fillna(0).sum(axis=1).pct_change().dropna()
print(
    f"\n[INFO] Retorno acumulado — método anterior: {(1 + naive_rets).prod() - 1:.1%} | "
    f"time-weighted: {(1 + strategy_rets).prod() - 1:.1%}"
)

last_vals = values.iloc[-1].dropna()
print(f"[INFO] Valor actual de la cartera auditada: $ {last_vals.sum():,.0f} ARS")
print(
    "[INFO] Pesos actuales:\n"
    + (last_vals / last_vals.sum())
    .sort_values(ascending=False)
    .map("{:.1%}".format)
    .to_string()
)

# --- BENCHMARK SINCRONIZADO (^MERV) ---
print("\n[INFO] Sincronizando Benchmark Merval...")
benchmark = yf.download("^MERV", start=start_str, auto_adjust=False, progress=False)[
    "Close"
].squeeze()
benchmark.index = pd.to_datetime(benchmark.index).tz_localize(None).normalize()

# Alinear NIVELES (NAV vs índice) en fechas comunes y recién ahí calcular
# retornos, para no comparar un retorno de 1 día contra uno de varios días.
nav = (1 + strategy_rets).cumprod()
base_date = px.index[px.index.get_loc(strategy_rets.index[0]) - 1]
nav.loc[base_date] = 1.0
levels = pd.concat([nav.sort_index(), benchmark], axis=1, join="inner").dropna()
levels.columns = ["Strategy", "Benchmark"]

# =====================================================================
# 3. REPORTE Y LIMPIEZA INSTITUCIONAL
# =====================================================================
combined = levels.pct_change().dropna()
combined.columns = ["Strategy", "Benchmark"]

qs.extend_pandas()

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# QuantStats solo abre el navegador cuando output=None (y en ese caso usa un
# archivo temporal). Como guardamos en REPORTS_DIR, lo abrimos nosotros.
OPEN_IN_BROWSER = True


def safe_html_report(report_name, *args, output_name, **kwargs):
    output_path = REPORTS_DIR / output_name
    method = getattr(qs.reports, report_name, None)

    if not callable(method):
        if report_name == "html_simple":
            print(
                "[WARN] html_simple no está disponible en esta versión de "
                "QuantStats; usando qs.reports.html() como fallback."
            )
            method = qs.reports.html
        else:
            print(
                f"[WARN] {report_name} no está disponible en esta versión de "
                "QuantStats; se omite este reporte HTML."
            )
            return None

    try:
        method(*args, output=str(output_path), **kwargs)
    except Exception as e:
        print(f"[ERROR] {report_name} falló: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None

    print(f"[OK] {report_name} -> {output_path}")
    if OPEN_IN_BROWSER:
        webbrowser.open(output_path.as_uri())
    return output_path


# REPORTS
# You can create 7 different report tearsheets:
# qs.reports.metrics(mode='basic|full", ...) - shows basic/full metrics
# qs.reports.plots(mode='basic|full", ...) - shows basic/full plots
# qs.reports.basic(...) - shows basic metrics and plots
# qs.reports.full(...) - shows full metrics and plots
# qs.reports.html(...) - generates a complete report as html

# can also be called via:
# stock.plot_snapshot(title='Facebook Performance', show=True)
qs.plots.snapshot(
    combined["Strategy"],
    benchmark=combined["Benchmark"],
    title="Estrategia vs Merval",
    show=True,
)

# Full metrics & plots (en consola, sin mostrar)
qs.reports.full(
    combined["Strategy"],
    benchmark=combined["Benchmark"],
    title="Estrategia vs Merval",
    show=False,
)

# --- Reportes HTML ---
safe_html_report(
    "html",
    combined["Strategy"],
    benchmark=combined["Benchmark"],
    title="Estrategia vs Merval",
    output_name="estrategia_vs_merval.html",
)

# Pro: Reporte simple (equity curve + métricas core)
safe_html_report(
    "html_simple",
    combined["Strategy"],
    benchmark=combined["Benchmark"],
    title="Estrategia vs Merval — Simple",
    output_name="estrategia_vs_merval_simple.html",
)

# Pro: Reporte Montecarlo multi-modelo (riesgo forward)
safe_html_report(
    "html_montecarlo",
    combined["Strategy"],
    title="Estrategia vs Merval — Montecarlo",
    output_name="estrategia_vs_merval_montecarlo.html",
)

# Pro: Alpha Decay
safe_html_report(
    "html_alpha_decay",
    combined["Strategy"],
    title="Estrategia vs Merval — Alpha Decay",
    output_name="estrategia_vs_merval_alpha_decay.html",
)
