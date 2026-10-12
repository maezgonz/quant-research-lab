### Optimizing Nancy Pelosi's Stock Portfolio in Python ###

# Libraries
import riskfolio as rp
import pandas as pd
import yfinance as yf

assets = [
    "PAM",
    "GGAL",
    "TGS",
    "YPF",
    "BMA",
    "EDN",
    "^MERV",  # SP500 benchmark
]

# Collect and format data
data = yf.download(assets, start="2024-01-01", end="2026-02-01")
data = data.loc[:, "Close"]
data

# Get returns
returns = data.pct_change(fill_method=None).dropna()
returns_bench = returns.pop("^MERV").to_frame()

# Riskfolio
port = rp.Portfolio(returns)
port.assets_stats(
    method_mu="hist",
    method_cov="hist",
    dict_cov={"d": 0.94},
)

port.benchindex = returns_bench

# Max Sharpe Portfolio
w = port.optimization(
    model="Classic",
    rm="CVaR",
    obj="Sharpe",
    hist=True,
    rf=0,
    l=0
)


ax = rp.plot_pie(
    w=w,
    others=0.05,
    nrow=25,
    cmap="tab20",
    height=6,
    width=10,
    ax=None
)

rp.plot_series(returns=returns, w=w)
rp.plot_drawdown(returns, w=w)
rp.plot_table(returns, w)
	