import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

df = yf.download(["BTC-USD","^GSPC"], start="2015-01-01")["Close"].interpolate().dropna()
df.columns = ["BTC","SP500"]
ath = df.cummax()
yr_low = df.rolling(365).min()
drawdown = df / ath - 1
upside = df/yr_low - 1
log_upside = np.log(df) - np.log(yr_low)
log_drawdown = np.log(df) - np.log(ath)

plt.style.use("dark_background")
fig, axes = plt.subplots(nrows=2, ncols=2,dpi=300, figsize=(14, 10))
log_drawdown.plot(ax=axes[0, 0], title="Log drawdown", lw=0.75, color=["orange","white"])
log_upside.plot(ax=axes[0, 1], title="Log Rolling 1yr Upside", lw=0.75, color=["orange","white"])
log_drawdown.plot.hist(ax=axes[1, 0], bins=100, alpha=0.8, legend=True, color=["orange","white"])
log_upside.plot.hist(ax=axes[1, 1], bins=100, alpha=0.8, legend=True, color=["orange","white"])
axes[1, 0].set_title("Log drawdown Histogram")
axes[1, 1].set_title("Log Rolling 1yr Upside Histogram")
plt.subplots_adjust(hspace=0.3, wspace=0.3)
for ax in axes.flatten():
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False, ncol=2, fontsize=10)

plt.show()