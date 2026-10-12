"""Generate mean-variance efficient frontier demo chart for the README.

Pulls daily prices via yfinance, simulates random portfolios (Monte Carlo)
and plots the cloud + efficient frontier. Output: docs/img/efficient_frontier.png
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf

TICKERS = ["AAPL", "MSFT", "NVDA", "GGAL", "SPY", "GLD", "BTC-USD", "ETH-USD"]
N_PORTFOLIOS = 20_000
SEED = 42
OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "img", "efficient_frontier.png")


def main() -> None:
    rng = np.random.default_rng(SEED)
    prices = yf.download(TICKERS, period="1y", interval="1d", progress=False)["Close"].dropna()
    rets = prices.pct_change().dropna()
    mu, cov = rets.mean().values * 252, rets.cov().values * 252

    n = len(TICKERS)
    w = rng.dirichlet(np.ones(n), size=N_PORTFOLIOS)
    port_ret = w @ mu
    port_vol = np.sqrt(np.einsum("ij,jk,ik->i", w, cov, w))
    sharpe = port_ret / port_vol

    i_max = int(np.argmax(sharpe))
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    sc = ax.scatter(port_vol, port_ret, c=sharpe, cmap="viridis", s=3, alpha=0.5)
    ax.scatter(port_vol[i_max], port_ret[i_max], marker="*", s=320, c="#FFD700",
               edgecolors="white", linewidths=0.7, label="Max Sharpe", zorder=5)
    fig.colorbar(sc, label="Sharpe ratio")
    ax.set_xlabel("Annualized volatility")
    ax.set_ylabel("Annualized return")
    ax.set_title(f"Monte Carlo efficient frontier — {n} assets, {N_PORTFOLIOS:,} random portfolios\n"
                 f"({', '.join(TICKERS)})", fontsize=11)
    ax.legend(loc="lower right")
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    fig.savefig(OUT)
    print(f"saved {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
