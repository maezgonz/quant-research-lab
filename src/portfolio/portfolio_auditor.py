import pandas as pd
import numpy as np
import requests
import yfinance as yf
import quantstats as qs
from tqdm import tqdm
from datetime import datetime
import warnings
import urllib3

warnings.filterwarnings("ignore")

# Desactivar advertencias de seguridad para sitios .gob.ar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
# 1. TABLA DE INFLACIÓN MENSUAL (HARDCODED)
# =====================================================================
INFLACION_DATA = {
    "2023-11-30": 12.80, "2023-12-31": 25.50, "2024-01-31": 20.60,
    "2024-02-29": 13.20, "2024-03-31": 11.00, "2024-04-30": 8.80,
    "2024-05-31": 4.20, "2024-06-30": 4.60, "2024-07-31": 4.00,
    "2024-08-31": 4.20, "2024-09-30": 3.50, "2024-10-31": 2.70,
    "2024-11-30": 2.40, "2024-12-31": 2.70, "2025-01-31": 2.20,
    "2025-02-28": 2.40, "2025-03-31": 3.70, "2025-04-30": 2.80,
    "2025-05-31": 1.50, "2025-07-31": 1.90, "2025-08-31": 1.90,
    "2025-09-30": 2.10, "2025-10-31": 2.30, "2025-11-30": 2.50,
    "2025-12-31": 2.80, "2026-01-31": 2.90, "2026-02-28": 2.90
}

# =====================================================================
# 2. PORTFOLIO
# =====================================================================
PORTFOLIO = [
    #STOCKS
    {'ticker': 'PAMP', 'cant': 999, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'EDN', 'cant': 1378, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'TGSU2', 'cant': 646, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'TGNO4', 'cant': 837, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'YPFD', 'cant': 111, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'METR', 'cant': 2545, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'GGAL', 'cant': 558, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'BMA', 'cant': 68, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'TRAN', 'cant': 182, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'MOLI', 'cant': 63, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'MORI', 'cant': 26867, 'start': '2023-10-10', 'tipo': 'stocks'},
    #BONDS
    {'ticker': 'AE38', 'cant': 3136, 'start': '2026-01-30', 'tipo': 'bonds'},
    {'ticker': 'AL41', 'cant': 4069, 'start': '2023-10-10', 'tipo': 'bonds'},
    {'ticker': 'AL30', 'cant': 6019, 'start': '2023-10-10', 'tipo': 'bonds'},
    {'ticker': 'GD30', 'cant': 6403, 'start': '2023-10-10', 'tipo': 'bonds'},
    #BOPREAL
    {'ticker': 'BPOA7', 'cant': 872, 'start': '2024-04-01', 'tipo': 'bonds', 'entry_px': 749.1373},
    {'ticker': 'BPOB7', 'cant': 883, 'start': '2024-04-01', 'tipo': 'bonds', 'entry_px': 749.1373},
    {'ticker': 'BPOC7', 'cant': 1308, 'start': '2024-04-01', 'tipo': 'bonds', 'entry_px': 749.1373},
    {'ticker': 'BPOD7', 'cant': 1327, 'start': '2024-04-01', 'tipo': 'bonds', 'entry_px': 749.1373},
    #NOTES
    {'ticker': 'S30N6', 'cant': 92539332, 'start': '2026-08-12', 'tipo': 'notes'},
]


# =====================================================================
# 3. LÓGICA DE AJUSTE POR INFLACIÓN (CORREGIDA)
# =====================================================================
def calculate_inflation_factor(dates):
    df_inf = pd.DataFrame(list(INFLACION_DATA.items()), columns=['date', 'value'])
    df_inf['date'] = pd.to_datetime(df_inf['date'])
    df_inf.set_index('date', inplace=True)
    df_inf.sort_index(inplace=True)

    # Cálculo de tasa diaria
    df_inf['daily_rate'] = (1 + df_inf['value'] / 100) ** (1 / 30) - 1

    # Crear serie diaria completa
    full_dates = pd.date_range(start=df_inf.index.min(), end=dates.max(), freq='D')

    # SOLUCIÓN AL ERROR: Reemplazamos .interpolate(method='ffill') por .ffill()
    # Además agregamos .bfill() para cubrir el inicio si es necesario
    df_daily = df_inf['daily_rate'].reindex(full_dates).ffill().bfill()

    cumulative_factor = (1 + df_daily).cumprod()
    return cumulative_factor.reindex(dates)


# =====================================================================
# 4. MOTOR DE AUDITORÍA
# =====================================================================
def run_real_alpha_audit():
    portfolio_values = pd.DataFrame()

    # Corregido: Agregado el ":" al final del for
    for asset in tqdm(PORTFOLIO, desc="Searching..."):
        try:
            url = f"https://data912.com/historical/{asset['tipo']}/{asset['ticker']}"
            r = requests.get(url, timeout=5).json()
            df = pd.DataFrame(r)
            t_col = 't' if 't' in df.columns else 'date'
            df['Date'] = pd.to_datetime(df[t_col], unit='s' if t_col == 't' else None)
            df.set_index('Date', inplace=True)

            prices = df['c' if 'c' in df.columns else 'close']
            if 'entry_px' in asset:
                prices.iloc[0] = asset['entry_px']

            portfolio_values[asset['ticker']] = prices[prices.index >= pd.to_datetime(asset['start'])] * asset['cant']
        except Exception:
            continue

    total_ars = portfolio_values.fillna(0).sum(axis=1)
    common_idx = total_ars.index

    inf_factor = calculate_inflation_factor(common_idx)
    mep_proxy = (yf.download("ARS=X", start=common_idx[0])['Close'] * 1.41).reindex(common_idx).ffill()

    rets_nominal = total_ars.pct_change().dropna()
    rets_real_ars = (total_ars / inf_factor).pct_change().dropna()
    rets_usd_mep = (total_ars / mep_proxy).pct_change().dropna()

    # =====================================================================
    # 5. GENERACIÓN DE REPORTES (FIX: Agregado de output para guardar HTML)
    # =====================================================================
    qs.extend_pandas()
    merval = yf.download("^MERV", start=common_idx[0])['Close'].pct_change().dropna()

    print("\n[OK] Generando Reportes...")

    qs.reports.full(rets_nominal, benchmark=merval, title='Portfolio: Nominal')
    qs.reports.full(rets_real_ars, title='Portfolio: Real (Inflación Hardcoded)')
    qs.reports.full(rets_usd_mep, title='Portfolio: Dólar MEP')

    print("\n[OK] Renderizando Reportes...")

    qs.reports.html(rets_nominal, benchmark=merval, title='Portfolio: Nominal')
    qs.reports.html(rets_real_ars, title='Portfolio: Real (Inflación Hardcoded)')
    qs.reports.html(rets_usd_mep, title='Portfolio: Dólar MEP')


if __name__ == "__main__":
    run_real_alpha_audit()