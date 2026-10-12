import numpy as np
import pandas as pd
from datetime import datetime

import vectorbt as vbt

# Prepare data
start = '2014-01-01 UTC'  # crypto is in UTC
end = '2026-03-14 UTC'
btc_price = vbt.YFData.download('BTC-USD', start=start, end=end).get('Close')

print(btc_price)

# We are going to test a simple Dual Moving Average Crossover (DMAC) strategy. For this, we are going to use MA class for calculating moving averages and generating signals. '
# Our first test is rather simple: buy when the 10-day moving average crosses above the 20-day moving average, and sell when opposite.')

fast_ma = vbt.MA.run(btc_price, 10, short_name='fast')
slow_ma = vbt.MA.run(btc_price, 20, short_name='slow')

entries = fast_ma.ma_crossed_above(slow_ma)
print(entries)

exits = fast_ma.ma_crossed_below(slow_ma)
print(exits)

pf = vbt.Portfolio.from_signals(btc_price, entries, exits)
pf.total_return()

# One strategy instance of DMAC produced one column in signals and one performance value.
# Adding one more strategy instance is as simple as adding one more column. Here we are passing an array of window sizes instead of a single value. For each window size in this array, it computes a moving average over the entire price series and stores it in a distinct column.

# Multiple strategy instances: (10, 30) and (20, 30)
fast_ma = vbt.MA.run(btc_price, [10, 20], short_name='fast')
slow_ma = vbt.MA.run(btc_price, [30, 30], short_name='slow')

entries = fast_ma.ma_crossed_above(slow_ma)
print(entries)

exits = fast_ma.ma_crossed_below(slow_ma)
print(exits)

pf = vbt.Portfolio.from_signals(btc_price, entries, exits)
pf.total_return()

# For the sake of convenience, VectorBT has created the column levels fast_window and slow_window for us to easily distinguish which window size corresponds to which column.
# Notice how signal generation part remains the same for each example - most functions in VectorBT work on time series of any shape. This allows creation of analysis pipelines that are universal to input data.
# The representation of different features as columns offers endless possibilities for backtesting. We could, for example, go a step further and conduct the same tests for Ethereum. To compare both instruments, combine price series for Bitcoin and Ethereum into one DataFrame and run the same backtesting pipeline.

# Multiple strategy instances and instruments
eth_price = vbt.YFData.download('ETH-USD', start=start, end=end).get('Close')
comb_price = btc_price.vbt.concat(eth_price,
    keys=pd.Index(['BTC', 'ETH'], name='symbol'))
comb_price.vbt.drop_levels(-1, inplace=True)
print(comb_price)

fast_ma = vbt.MA.run(comb_price, [10, 20], short_name='fast')
slow_ma = vbt.MA.run(comb_price, [30, 30], short_name='slow')

entries = fast_ma.ma_crossed_above(slow_ma)
print(entries)

exits = fast_ma.ma_crossed_below(slow_ma)
print(exits)

pf = vbt.Portfolio.from_signals(comb_price, entries, exits)
pf.total_return()

mean_return = pf.total_return().groupby('symbol').mean()
mean_return.vbt.barplot(xaxis_title='Symbol', yaxis_title='Mean total return')

# Not only strategies and instruments can act as separate features, but also time. If we want to find out when our strategy performs best, it's reasonable to backtest over multiple time periods. VectorBT allows us to split one time period into many, given they have the same length and frequency, and represent them as distinct columns. For example, let's split the whole time period into two equal time periods and backest them at once.
# Multiple strategy instances, instruments, and time periods
mult_comb_price, _ = comb_price.vbt.range_split(n=2)
print(mult_comb_price)

fast_ma = vbt.MA.run(mult_comb_price, [10, 20], short_name='fast')
slow_ma = vbt.MA.run(mult_comb_price, [30, 30], short_name='slow')

entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

pf = vbt.Portfolio.from_signals(mult_comb_price, entries, exits, freq='1D')
pf.total_return()

# Notice how index is no more datetime-like, since it captures multiple time periods. That's why it's required here to pass the frequency freq to the Portfolio class in order to be able to compute performance metrics such as the Sharpe ratio.
# The index hierarchy of the final performance series can be then used to group the performance by any feature, such as window pair, symbol, and time period.
mean_return = pf.total_return().groupby(['split_idx', 'symbol']).mean()
mean_return.unstack(level=-1).vbt.barplot(
    xaxis_title='Split index',
    yaxis_title='Mean total return',
    legend_title_text='Symbol')

# There is much more to backtesting than simply stacking columns: VectorBT offers functions for most parts of a backtesting pipeline - from building indicators and generating signals, to modeling portfolio performance and visualizing results.