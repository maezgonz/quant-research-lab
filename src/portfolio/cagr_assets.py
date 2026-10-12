import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date, timedelta

# --- CONFIGURACIÓN DE USUARIO ---
años = 20
capital_inicial = 10_000_000
fee_byma = 0.0005  # 0.05% por operación
start = date.today() - timedelta(days=365*años)
tickers = ["GGAL", "BMA", "YPF", "PAM", "TGS", "CRESY", "IRS", "TEO", "MELI", "EDN", "BBAR", "CEPU", "TX", "SUPV", "LOMA"]

# --- DATA FETCHING ---
data = yf.download(tickers, start=start, interval="1wk")['Close'].dropna(how='all')
yields = data.pct_change().fillna(0)

# --- ESTRATEGIA VECTORIZADA (ELITE SPEED) ---
def simulate_rotation(yields_df, top_k=5, momentum=True):
    ranks = yields_df.shift(1).rank(axis=1, ascending=not momentum)
    mask = ranks <= top_k
    # Retorno bruto
    port_yield = (yields_df * mask).sum(axis=1) / top_k
    # Costo de rotación (estimación simple: cuando cambia la máscara)
    trades = mask.diff().fillna(0).abs().sum(axis=1) / 2
    costs = trades * fee_byma
    return port_yield - costs

# Ejecución
yields['BuyHold'] = yields.mean(axis=1)
yields['Best5'] = simulate_rotation(yields, top_k=5, momentum=True)
yields['Worst5'] = simulate_rotation(yields, top_k=5, momentum=False)

# --- KPI ENGINE ---
def get_advanced_stats(rets):
    cagr = (rets + 1).prod()**(1/años) - 1
    vol = rets.std() * np.sqrt(52)
    sharpe = cagr / vol
    cum_ret = (rets + 1).cumprod()
    dd = (cum_ret / cum_ret.cummax()) - 1
    max_dd = dd.min()
    winrate = len(rets[rets > 0]) / len(rets)
    return [cagr, vol, sharpe, max_dd, winrate]

stats = pd.DataFrame({
    'Buy & Hold': get_advanced_stats(yields['BuyHold']),
    'Best 5': get_advanced_stats(yields['Best5']),
    'Worst 5': get_advanced_stats(yields['Worst5'])
}, index=['CAGR', 'Volatilidad', 'Sharpe', 'Max Drawdown', 'Winrate'])

print("📊 KPIs INSTITUCIONALES:")
print(stats)

# --- PLOTS AVANZADOS ---
plt.style.use('default')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(21, 12), sharex=True)

# Equity Curve
(yields[['BuyHold', 'Best5', 'Worst5']] + 1).cumprod().plot(ax=ax1, color=['gray', 'lime', 'red'])
ax1.set_title("Evolución del Capital (Log Scale)")
ax1.set_yscale('log')

# Underwater Plot
((yields[['BuyHold', 'Best5', 'Worst5']] + 1).cumprod() /
 (yields[['BuyHold', 'Best5', 'Worst5']] + 1).cumprod().cummax() - 1).plot(ax=ax2, kind='area', alpha=0.3)
ax2.set_title("Drawdown (Riesgo de Ruina)")

plt.tight_layout()
plt.show()