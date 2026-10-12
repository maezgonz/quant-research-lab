import os

# Silenciamos el aviso de KMeans en Windows antes de importar sklearn
os.environ["OMP_NUM_THREADS"] = "1"

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import multiprocessing

# --- CONFIGURACIÓN ---
sns.set_style('whitegrid')
tickers = ['BCH-USD', 'EOS-USD', 'BTG-USD', 'TRX-USD', 'LTC-USD', 'NEO-USD']
index_ticker = 'BTC-USD'

num_simulations = 1000
min_weight_asset = 0.01
max_weight_asset = 0.5
min_good_alpha = 0.005
risk_free_rate = 0.025
start_date = '2019-01-01'
end_date = '2026-01-01'


# --- FUNCIONES ---

def download_data_yf(tickers, index_ticker, start, end):
    print(f"Descargando datos desde Yahoo Finance...")
    all_tickers = tickers + [index_ticker]
    raw_data = yf.download(all_tickers, start=start, end=end, progress=True)

    if raw_data.empty:
        raise ValueError("No se descargaron datos.")

    data = raw_data['Adj Close'] if 'Adj Close' in raw_data.columns else raw_data['Close']

    prices = data[tickers].dropna()
    index_prices = data[[index_ticker]].dropna()

    common_index = prices.index.intersection(index_prices.index)
    return prices.loc[common_index], index_prices.loc[common_index]


def portfolio_metrics(w, p_id, prices_df, index_df):
    rets = prices_df.pct_change().dropna()
    mkt_rets = index_df.pct_change().dropna().values.flatten()

    port_rets = rets.dot(w).values

    min_len = min(len(port_rets), len(mkt_rets))
    port_rets = port_rets[:min_len]
    mkt_rets = mkt_rets[:min_len]

    eq_port = np.cumprod(1.0 + port_rets)
    eq_mkt = np.cumprod(1.0 + mkt_rets)

    # --- CÁLCULO DE MAX DRAWDOWN ---
    # Encontramos el máximo acumulado hasta cada punto
    rolling_max = np.maximum.accumulate(eq_port)
    drawdowns = (eq_port - rolling_max) / rolling_max
    max_drawdown = np.min(drawdowns)

    p_ret_total = eq_port[-1] - 1
    num_years = len(port_rets) / 365.0

    ann_p_ret = (1 + p_ret_total) ** (1 / num_years) - 1
    ann_m_ret = (eq_mkt[-1] ** (1 / num_years)) - 1

    beta = np.cov(port_rets, mkt_rets)[0, 1] / np.var(mkt_rets)
    er = risk_free_rate + beta * (ann_m_ret - risk_free_rate)
    alpha = ann_p_ret - er

    return (alpha, beta, p_ret_total, eq_port.tolist(), p_id, max_drawdown)


def mc_simulation(num_portfolios, prices_df, index_df):
    print(f"Iniciando simulación de {num_portfolios} portafolios...")
    params_list = []
    for i in range(num_portfolios):
        w = np.random.random(len(tickers))
        w /= np.sum(w)
        while np.any(w < min_weight_asset) or np.any(w > max_weight_asset):
            w = np.random.random(len(tickers))
            w /= np.sum(w)
        params_list.append((w, i, prices_df, index_df))

    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        results = pool.starmap(portfolio_metrics, params_list)

    data_res = []
    for r in results:
        idx = r[4]
        weights = list(params_list[idx][0])
        # r[5] es el Max Drawdown
        data_res.append([r[0], r[1], r[2], r[5]] + weights)

    df = pd.DataFrame(data_res, columns=['alpha', 'beta', 'return', 'max_dd'] + tickers)
    return df.sort_values('alpha', ascending=False), results


def perform_clustering(mc_df):
    print("Analizando clusters...")
    good_p = mc_df.head(min(200, len(mc_df))).copy()
    X = good_p[['alpha', 'beta']]
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=4, random_state=42, n_init=10).fit(X_scaled)
    good_p['cluster'] = km.labels_

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=good_p, x='beta', y='alpha', hue='cluster', palette='viridis', s=100)
    plt.title("Clustering Alpha vs Beta (Estrategias Top)")
    plt.show()
    return good_p


if __name__ == '__main__':
    prices, index = download_data_yf(tickers, index_ticker, start_date, end_date)

    if not prices.empty:
        mc_result, raw_data = mc_simulation(num_simulations, prices, index)
        clustered_df = perform_clustering(mc_result)

        best = mc_result.iloc[0]
        print("\n" + "=" * 40)
        print("ESTRATEGIA ÓPTIMA (MAX ALPHA)")
        print(f"Alpha Anual: {best.alpha:.2%}")
        print(f"Beta vs Mkt: {best.beta:.4f}")
        print(f"Retorno Tot: {best['return']:.2%}")
        print(f"Max Drawdown: {best.max_dd:.2%}")  # <-- NUEVA MÉTRICA
        print("=" * 40)

        # Gráfico final
        best_equity = next(r[3] for r in raw_data if r[0] == best.alpha)
        plt.figure(figsize=(12, 6))
        plt.plot(best_equity, label='Mejor Portafolio Simulado', color='darkblue')
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Capital Inicial')
        plt.title(f"Evolución del Capital (Retorno: {best['return']:.0%})")
        plt.ylabel("Multiplicador de Capital")
        plt.legend()
        plt.show()