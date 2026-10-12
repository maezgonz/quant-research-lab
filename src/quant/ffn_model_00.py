import ffn
import matplotlib.pyplot as plt

#%matplotlib inline

# download price data from Yahoo! Finance. By default,
# the Adj. Close will be used.
prices = ffn.get('ggal,bma', start='2010-01-01')

# let's compare the relative performance of each stock
# we will rebase here to get a common starting point for both securities
ax = prices.rebase().plot(figsize=(10, 5))
plt.show()

# now what do the return distributions look like?
returns = prices.to_returns().dropna()
ax = returns.hist(figsize=(10, 5))

# ok now what about some performance metrics?
stats = prices.calc_stats()
stats.display()

# what about the drawdowns?
ax = stats.prices.to_drawdown_series().plot(figsize=(10, 5))
plt.show()