# Creating a Stock Portfolio
import numpy as np
import pandas as pd
import yfinance as yf
import riskfolio as rp
import warnings

warnings.filterwarnings("ignore")

# Date Range
start = '2016-01-01'
end = '2019-12-30'

# Ticker of Assets
assets = ['JCI', 'TGT', 'CMCSA', 'CPB', 'MO', 'APA', 'MMC', 'JPM', 'ZION', 'PSA', 'BAX', 'BMY',
          'LUV', 'PCAR', 'TXT', 'TMO', 'DE', 'MSFT', 'HPQ','SEE', 'VZ', 'CNP', 'NI', 'T', 'BA']
assets.sort()

# Tickers of Factors
factors = ['MTUM', 'QUAL', 'VLUE', 'SIZE', 'USMV']
factors.sort()

tickers = assets + factors
tickers.sort()

# Downloading the Data
data = yf.download(tickers, start = start, end = end)
data = data.loc[:,('Close', slice(None))]
data.columns = tickers
returns = data.pct_change().dropna()

Y = returns[assets]
X = returns[factors]

# Creating the Portfolio Object
port = rp.Portfolio(returns=Y)

# To display dataframes values in percentage format
pd.options.display.float_format = '{:.4%}'.format

# Choose the Risk Measure
rm = 'MSV' # Semi Standard Deviation

# Estimate Inputs of The Model (historical estimates)
method_mu='hist' # Method to estimate expected returns based on historical data.
method_cov='hist' # Method to estimate covariance matrix based on historical data.

port.assets_stats(method_mu=method_mu,
                  method_cov=method_cov)

# Portfolio Optimization

# Choose the Risk Measure
rm = 'MSV' # Semi Standard Deviation

# Estimate Inputs of Model (Historical Estimates)
method_mu='hist' # Method to estimate expected returns based on historical data.
method_cov='hist' # Method to estimate covariance matrix based on historical data.

port.assets_stats (method_mu=method_mu, method_cov=method_cov)

mu = port.mu
cov = port.cov

# Estimate the Portfolio that Maximizes the Risk Adjusted Return Ratio
w1 = port.optimization(model='Classic', rm=rm, obj='Sharpe', rf=0.0, l=0, hist=True)

# Estimate Points in the Efficient Mean - Semi Standard Deviation
ws = port.efficient_frontier(model='Classic', rm=rm, points=20, rf=0, hist=True)

# Estimate the Risk Parity Portfolio for Semi Standard Deviation 
w2 = port.rp_optimization(model='Classic', rm=rm, rf=0, b=None, hist=True)

# Estimate the Portfolio that Maximizes the Risk Adjusted Return Ratio
w2 = port.rp_optimization(model='Classic', rm=rm, rf=0, b=None, hist=True)

# Estimate the Risk Parity Portfolio for Risk Factors
port.factors = X
port.factors_stats(method_mu=method_mu, 
                   method_cov=method_cov,
                   feature_selection='stepwise',
                   dict_risk=dict(stepwise='Foward'))
w3 = port.rp_optimization(model='FC', rm='MV', rf=0, b_f=None)

# Estimate the Risk Parity Portfolio for Principal Components
port.factors = X
port.factors_stats(method_mu=method_mu, 
                   method_cov=method_cov,
                   feature_selection='PCR',
                   dict_risk=dict(n_components=0.95))
w4 = port.rp_optimization(model='FC', rm='MV', rf=0, b_f=None)

