# Portfolio Optimization

# Choose the Risk Measure
rm = 'MSV' # Semi Standard Deviation

# Estimate Inputs of Model (Historical Estimates)
method_mu='hist' # Method to estimate expected returns based on historical data.
method_cov='hist' # Method to estimate covariance matrix based on historical data.

port.assets_stats (method_mu=method_mu, method_cov=method_cov, d=0.94)

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
