#====================
# Import
#====================

import ffn
import matplotlib.pyplot as plt
#%matplotlib inline

#====================
# Data Retrieval
#====================

data = ffn.get('agg,hyg,spy,eem,efa', start='2010-01-01', end='2026-03-21')
print(data.head())

print(ffn.get('aapl:Open,aapl:High,aapl:Low,aapl:Close', start='2010-03-21', end='2026-02-06').head())

data = ffn.get('dbc', provider=ffn.data.csv, path='test_data.csv', existing=data)
print(data.head())

#====================
#Data Manipulation
#====================

returns = data.to_log_returns().dropna()
print(returns.head())

ax = returns.hist(figsize=(12, 5))

returns.corr().as_format('.2f')

returns.plot_corr_heatmap();

ax = data.rebase().plot(figsize=(12,5))

#=============================
# Performance Measurement
#=============================

perf = data.calc_stats()
perf.plot();

print(perf.display())

# we can also use perf[2] in this case
perf['spy'].display_monthly_returns()

perf[2].plot_histogram();
perf['spy'].stats

#==============================================
# Numerical Routines and Financial Functions
#==============================================

returns.calc_mean_var_weights().as_format('.2%')
returns.calc_ftca(threshold=0.8)
{1: ['eem', 'spy', 'efa'], 2: ['agg'], 3: ['dbc'], 4: ['hyg']}