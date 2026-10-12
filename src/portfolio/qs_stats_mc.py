import quantstats as qs
import pandas as pd

# 1. Configuración y Extensión de Pandas
#qs.extend_pandas()

# 2. Descarga de Retornos (GGAL vs Benchmark SPY)
# Usamos un benchmark para dar contexto al retorno
#stock = qs.utils.download_returns('GGAL')
#benchmark = qs.utils.download_returns('SPY')

# fetch daily returns
returns = qs.utils.download_returns("GGAL")

# run Monte Carlo simulation with 1000 paths
mc = qs.stats.montecarlo(returns, sims=10, seed=42)

# view terminal value statistics
print(mc.stats)

# Set bust threshold at -20% drawdown, goal at +50% return
mc = qs.stats.montecarlo(returns, sims=10, bust=-0.20, goal=0.50, seed=42)
print(f"Probability of bust: {mc.bust_probability:.1%}")
print(f"Probability of reaching goal: {mc.goal_probability:.1%}")
print(mc.maxdd)

# Confidence Bands
# Get confidence intervals for the simulation paths: 95% confidence band
lower, upper = mc.confidence_band(0.95)

# specific percentile path
p10 = mc.percentile(10)  # 10th percentile path
p90 = mc.percentile(90)  # 90th percentile path

qs.plots.montecarlo(returns, sims=10, seed=42)

# or from an existing result
mc.plot()

# plot terminal value distribution:
qs.plots.montecarlo_distribution(returns, sims=10, seed=42)

# Pandas Extension
# After calling qs.extend_pandas(), you can use Monte Carlo directly on Series:

qs.extend_pandas()

# run simulation directly on a returns Series
mc = returns.montecarlo(sims=10, bust=-0.15, goal=0.30)

# plot directly
returns.plot_montecarlo(sims=500)

# Sharpe, Drawdown & CAGR Distributions
# Get distributions of key metrics across simulations:

# Sharpe ratio distribution
sharpe_dist = qs.stats.montecarlo_sharpe(returns, sims=10)
print(f"Sharpe range: {sharpe_dist['percentile_5']:.2f} to {sharpe_dist['percentile_95']:.2f}")

# Max drawdown distribution
dd_dist = qs.stats.montecarlo_drawdown(returns, sims=10)
print(f"Drawdown range: {dd_dist['percentile_5']:.1%} to {dd_dist['percentile_95']:.1%}")

# CAGR distribution
cagr_dist = qs.stats.montecarlo_cagr(returns, sims=10)
print(f"CAGR range: {cagr_dist['percentile_5']:.1%} to {cagr_dist['percentile_95']:.1%}")

# Access Raw Data
# The raw simulation data is available as a DataFrame:

print(mc.data.head())