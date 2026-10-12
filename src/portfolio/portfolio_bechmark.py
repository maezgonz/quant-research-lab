import pandas as pd
import numpy as np
import requests
import yfinance as yf
import quantstats as qs
from tqdm import tqdm
import os
import re
import webbrowser
import warnings

warnings.filterwarnings("ignore")

# =====================================================================
# 1. TABLA DE INFLACIÓN "FUENTES OFICIALES" (HARDCODED)
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
# 2. POSICIÓN DE PORTFOLIO HARDCODEADA
# =====================================================================
PORTFOLIO = [
    # Acciones (Compras Oct-23)
    {'ticker': 'PAMP', 'cant': 999, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'GGAL', 'cant': 558, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'YPFD', 'cant': 111, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'TGSU2', 'cant': 646, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'METR', 'cant': 2545, 'start': '2023-10-10', 'tipo': 'stocks'},
    {'ticker': 'MORI', 'cant': 26867, 'start': '2023-10-10', 'tipo': 'stocks'},
    # Bonos y Bopreales (Hardcoded entry $749.1373)
    {'ticker': 'BPOA7', 'cant': 872, 'start': '2024-04-01', 'tipo': 'bonds', 'entry': 749.1373},
    {'ticker': 'BPOB7', 'cant': 883, 'start': '2024-04-01', 'tipo': 'bonds', 'entry': 749.1373},
    {'ticker': 'BPOC7', 'cant': 1308, 'start': '2024-04-01', 'tipo': 'bonds', 'entry': 749.1373},
    {'ticker': 'BPOD7', 'cant': 1327, 'start': '2024-04-01', 'tipo': 'bonds', 'entry': 749.1373},
    {'ticker': 'AL30', 'cant': 6019, 'start': '2023-10-10', 'tipo': 'bonds'},
    {'ticker': 'GD30', 'cant': 6403, 'start': '2023-10-10', 'tipo': 'bonds'},
    # Letras (S17A6 Actualizada)
    {'ticker': 'S17A6', 'cant': 30057904, 'start': '2026-02-01', 'tipo': 'notes'}
]


# =====================================================================
# 3. FUNCIONES CORE
# =====================================================================
def calculate_inflation_factor(dates):
    """Genera factor de descuento diario basado en tu tabla."""
    df_inf = pd.DataFrame(list(INFLACION_DATA.items()), columns=['date', 'value'])
    df_inf['date'] = pd.to_datetime(df_inf['date'])
    df_inf.set_index('date', inplace=True)
    df_inf['daily_rate'] = (1 + df_inf['value'] / 100) ** (1 / 30) - 1
    full_range = pd.date_range(start=dates.min(), end=dates.max(), freq='D')
    df_daily = df_inf['daily_rate'].reindex(full_range).ffill().bfill()
    return (1 + df_daily).cumprod().reindex(dates)


def get_data912(ticker, tipo):
    endpoint = 'live_arg_notes' if tipo == 'notes' else f'historical/{tipo}'
    try:
        r = requests.get(f"https://data912.com/{endpoint}/{ticker}", timeout=10)
        df = pd.DataFrame(r.json())
        t_col = 't' if 't' in df.columns else 'date'
        df['Date'] = pd.to_datetime(df[t_col], unit='s' if t_col == 't' else None)
        df.set_index('Date', inplace=True)
        return df['c' if 'c' in df.columns else 'close']
    except Exception:
        return pd.Series()


# =====================================================================
# 4. PROCESAMIENTO Y REPORTES
# =====================================================================
def run_quant_terminal():
    print(f"🚀 Auditoría..")
    portfolio_values = pd.DataFrame()

    for asset in tqdm(PORTFOLIO, desc="Procesando Activos"):
        prices = get_data912(asset['ticker'], asset['tipo'])
        if not prices.empty:
            p_slice = prices[prices.index >= pd.to_datetime(asset['start'])].copy()
            if 'entry' in asset: p_slice.iloc[0] = asset['entry']

            val = (p_slice * asset['cant']) / 100 if asset['tipo'] in ['bonds', 'notes'] else p_slice * asset['cant']
            portfolio_values[asset['ticker']] = val

    total_ars = portfolio_values.fillna(method='ffill').sum(axis=1)
    common_idx = total_ars.index

    # Sincronización Benchmark (IMV/^MERV)
    benchmark = yf.download("^MERV", start=common_idx[0])['Close']

    # Ajuste por Inflación Real
    inf_factor = calculate_inflation_factor(common_idx)
    total_real = total_ars / inf_factor

    # Preparación de Retornos
    rets_strat = total_ars.pct_change().dropna()
    rets_real = total_real.pct_change().dropna()
    rets_bench = benchmark.pct_change().dropna()

    # Generación de Reporte QuantStats
    qs.extend_pandas()
    report_file = "Auditoria_Gonzalez_93M.html"
    qs.reports.html(rets_strat, benchmark=rets_bench, output=report_file,
                    title="Auditoría Real vs Benchmark (Matias Gonzalez)")

    # Limpieza de Marca de Agua
    if os.path.exists(report_file):
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'Generated by <a href="https://github.com/ranaroussi/quantstats">QuantStats</a>', '', content)
        content = re.sub(r'\(v\. \d+\.\d+\.\d+\)', '', content)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        webbrowser.open(f"file://{os.path.abspath(report_file)}")

    # KPIs Críticos por Consola
    print(f"\n📊 RESUMEN:")
    print(f"• Retorno Acumulado: {qs.stats.comp(rets_strat) * 100:.2f}%")
    print(f"• Sharpe Ratio: {qs.stats.sharpe(rets_strat):.2f}")
    print(f"• Sortino Ratio: {qs.stats.sortino(rets_strat):.2f}")
    print(f"• Max Drawdown: {qs.stats.max_drawdown(rets_strat) * 100:.2f}%")
    print(f"• Alpha vs Merval: {rets_strat.alpha(rets_bench):.2f}")


if __name__ == "__main__":
    run_quant_terminal()