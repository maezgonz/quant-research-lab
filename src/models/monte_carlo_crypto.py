# -*- coding: utf-8 -*-
"""Crypto portfolio Monte-Carlo simulation (originally a Colab notebook).

1. tickers - assets that we use in a portfolio
2. index_ticker - our market benchmark
3. num_simulations - number of the simulated portfolios
"""

import os
import requests
import pdb;
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.optimize import minimize
from multiprocessing import Pool
import multiprocessing
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

sns.set_style('darkgrid')

tickers = ['BCH', 'EOS' , 'BTG', 'TRX', 'LTC', 'NEO', 'VERI', 'SALT','ETP']

index_ticker = 'usdt'

num_simulations = 1000
min_weight_asset = 0.01
max_weight_asset = 0.5
min_good_alpha = 0.005
rolled_sortino_period = 63

"""### Main functions

1. download_data - getting data from https://financialmodelingprep.com
2. plot_prices - plotting the data relatively to a first value (starts from 1.0)
3. portfolio_metrics - calculating basic metrics (alpha, beta, returns, equities) for the current given price data
4. mc_simulation - Monte-Carlo simulation of the portfolios using portfolio_metrics function in multiprocessing mode
5. define_num_clusters - selecting the number of clusters based on silhouette score
6. do_cluster_analysis - cluster analysis of portfolios. The items are weighted by alpha
7. get_best_solutions - calculation the equity of best solutions (portfolios) as the centers of clusters
8. sortino_ratio - calculation the Sortino ratio
9. rolling_sortino_portfolio - calculation the rolling Sortino ratio for portfolios
"""

def download_data(tickers, start_date, end_date, price_column):
  prices = pd.DataFrame(columns = tickers)
  # Financial Modeling Prep API key via environment variable
  apiKey = os.getenv("FMP_API_KEY", "")
  for t in tickers:
    req_str = 'https://financialmodelingprep.com/api/v3/historical-price-full/{}?from={}&to={}&apikey={}'.format(t, start_date, end_date,apiKey)
    print(req_str)
    json = requests.get(req_str, timeout=15).json()
    prices[t] = pd.DataFrame(json['historical'])[price_column]

  return prices

def plot_prices(asset_prices):
  ap_normed = prices[1:] / prices.iloc[0]

  plt.figure(figsize=(15,10))
  for t in tickers:
    plt.plot(ap_normed[t])

  plt.legend(asset_prices.columns)
  plt.title('Asset Curves ({} - {})'.format(start_date, end_date))

def portfolio_metrics(*params):
  w = params[:len(tickers)]

  portfolio_returns = np.array(prices.pct_change().multiply(w, axis=1).sum(axis=1))
  portfolio_returns[0] = 0.0

  market_returns = np.array(index_prices.pct_change()).squeeze()
  market_returns[0] = 0.0

  equity_portfolio = np.cumprod(1.0 + portfolio_returns)
  equity_market = np.cumprod(1.0 + market_returns)

  p_return = equity_portfolio[-1] / equity_portfolio[0] - 1
  m_return = equity_market[-1] / equity_market[0] - 1
  num_years = len(market_returns) / 252.0
  e_pr = p_return * (1 / num_years) - 1
  e_m = m_return * (1 / num_years) - 1

  beta = np.cov(portfolio_returns, market_returns)[0, 1] / np.var(market_returns)
  er = risk_free_rate + beta * (e_m - risk_free_rate)
  ##ALE CHANGE
  ##remove the absolute error and review why return a negative value
  alpha = abs(e_pr - er)
  return (alpha, beta, p_return, m_return, equity_portfolio, equity_market, int(params[-1]))

def define_num_clusters():
  item_multiplier = 1000
  if min_good_alpha != 0:
    item_multiplier = 1.0 / min_good_alpha

  good_portfolios = mc_result[mc_result.alpha > min_good_alpha]
  X = pd.DataFrame()

  for i in range(0, good_portfolios.shape[0]):
    X = X.append([good_portfolios[tickers].iloc[i]] * int(round(item_multiplier * good_portfolios['alpha'].iloc[i])))

  mms = MinMaxScaler()
  mms.fit(X)
  X_transformed = mms.transform(X)

  sum_of_squared_distances = []
  silhouette_scores = []
  num_clusters = range(2, 20)

  for k in num_clusters:
    km = KMeans(n_clusters = k, random_state = 100, n_jobs = -1)
    km = km.fit(X_transformed)

    silhouette_scores.append(silhouette_score(X_transformed, km.labels_, metric = 'euclidean'))
    sum_of_squared_distances.append(km.inertia_)

  k = num_clusters[np.argmax(silhouette_scores)]
  print('Optimal number of clusters: ' + str(k))

  sns.set(rc = {'figure.figsize':(15, 10)})
  plt.plot(num_clusters, sum_of_squared_distances, 'bx-')
  plt.xlabel('Number of Clusters')
  plt.ylabel('Sum of Squared Distances')
  plt.title('Elbow Method for Optimal Number of Clusters')
  plt.show()

  plt.plot(num_clusters, silhouette_scores, 'bx-')
  plt.xlabel('Number of Clusters')
  plt.ylabel('Silhouette Score')
  plt.title('Silhouette Score of Clusters')
  plt.show()

  return k, mms, X_transformed, good_portfolios

def do_cluster_analysis(k, mms, X_transformed, good_portfolios):
  km = KMeans(n_clusters = k, random_state = 100)
  km = km.fit(X_transformed)
  cluster_centers = mms.inverse_transform(km.cluster_centers_)

  mean_cols = [str(col) for col in tickers]
  df_result = pd.DataFrame(columns = mean_cols, data = cluster_centers)
  df_result['num_objects'] = [0.0] * df_result.shape[0]
  df_result['avg_alpha'] = [0.0] * df_result.shape[0]

  tmp_transformed = mms.transform(good_portfolios[tickers])
  for i in range(0, df_result.shape[0]):
    clusted_ind = km.predict(tmp_transformed) == i
    df_result['num_objects'][i] = np.sum(clusted_ind)
    df_result['avg_alpha'][i] = np.mean(good_portfolios['alpha'][clusted_ind])

  return df_result

def get_best_solutions(clusters, num_clusters, mc_best):
  asset_returns = prices.pct_change()
  asset_returns.iloc[0] = 0.0

  best_portfolios = pd.DataFrame(columns = [range(0, num_clusters)].append([index_ticker]), index=prices.index)
  for i in range(0, clusters.shape[0]):
    w = clusters.iloc[i][tickers]
    portfolio_returns = asset_returns.multiply(w, axis=1).sum(axis=1)
    equity_portfolio = np.cumprod(1.0 + portfolio_returns)
    best_portfolios[i] = equity_portfolio
  best_portfolios[index_ticker] = mc_best[5]

  best_portfolios.plot()
  plt.legend()
  plt.title('Best solutions vs. Index ({} - {})'.format(start_date, end_date))

  return best_portfolios

def sortino_ratio(returns):
  losses = returns[returns <= 0]
  downside_deviation = np.std(losses)

  return np.mean(returns) / downside_deviation * np.sqrt(252)

def rolling_sortino_portfolio(portfolios):
  rolled_sortino = pd.DataFrame()
  port_returns = portfolios.pct_change().dropna()

  for p in portfolios.columns:
    rolled_sortino[p] = port_returns[p].rolling(rolled_sortino_period).apply(sortino_ratio)
  return rolled_sortino

"""### Preliminary analysis, Monte-Carlo simulation

Download and plot the data. Calculate the beta between assets.
"""

start_date = '2004-09-29'
start_date = '2018-09-29'
end_date = '2021-08-06'
risk_free_rate = 0.025

prices = download_data(tickers, start_date, end_date, 'adjClose')
index_prices = download_data([index_ticker], start_date, end_date, 'adjClose')
plot_prices(prices.join(index_prices))

betas = pd.DataFrame(columns=tickers, index=tickers)
for x in range(0, len(tickers)):
  for y in range(0, len(tickers)):
    returns_x = prices[tickers[x]].pct_change().dropna()
    returns_y = prices[tickers[y]].pct_change().dropna()
    betas[tickers[x]][tickers[y]] = np.cov(returns_y, returns_x)[0, 1] / np.var(returns_x)

plt.figure(figsize=(15,15))
sns.heatmap(betas.astype(float), annot=True)

"""Run the Monte-Carlo simulation.
Plot the best portfolio.
"""

def mc_simulation(num_portfolios):
  mc_portfolios = np.zeros((num_portfolios, len(tickers) + 3))

  num_satisfied_portfolios = 0
  while (num_satisfied_portfolios != num_portfolios):
    weights = np.array(np.random.random(len(tickers)))
    weights = weights / np.sum(weights)
    if np.sum(weights < min_weight_asset) == 0 and np.sum(weights > max_weight_asset) == 0:
      mc_portfolios[num_satisfied_portfolios, :len(tickers)] = weights
      num_satisfied_portfolios = num_satisfied_portfolios + 1

  params = ()
  for p in range(0, num_portfolios):
    params = ((np.append(mc_portfolios[p, :len(tickers)], [p])),) + params

  with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
    print('5')
    metrics = p.starmap(portfolio_metrics, params[1:])

  print('6')
  for i in range(0, len(metrics)):
    ind = metrics[i][-1]
    mc_portfolios[ind, -3] = metrics[i][0]
    mc_portfolios[ind, -2] = metrics[i][1]
    mc_portfolios[ind, -1] = metrics[i][2]

  print('7')
  mc_portfolios_df = pd.DataFrame(mc_portfolios, columns=tickers + ['alpha', 'beta', 'return'])
  print('8')
  return mc_portfolios_df.sort_values('alpha', ascending=False)


mc_result = mc_simulation(num_simulations)

sns.set(rc = {'figure.figsize':(15, 10)})
sns.distplot(mc_result.alpha)
mc_result

w_best = np.append(mc_result.iloc[0][:len(tickers)], 0)
output_best = portfolio_metrics(*w_best)

plt.figure(figsize=(15,10))
plt.plot(output_best[4], color='dodgerblue')
plt.plot(output_best[5], color='lightcoral')
plt.legend(['Portfolio', index_ticker])
plt.ylabel('Capital')
plt.title('Best portfolio vs. Index ({} - {})'.format(start_date, end_date))

print('Alpha is {}'.format(output_best[0]))
print('Portfolio return is {}'.format(output_best[2]))
print('Market return is {}'.format(output_best[3]))
print('Best weights:\n{}'.format(w_best[:len(tickers)]))

"""### Define the number of clusters and carry out the analysis"""

num_clusters, scaler, X_trans, good_portfolios = define_num_clusters()
clusters = do_cluster_analysis(num_clusters, scaler, X_trans, good_portfolios)
print(good_portfolios.shape)

"""### Creating the best solutions"""

best_portfolios = get_best_solutions(clusters, num_clusters, output_best)
best_portfolios

"""Calculating the rolling Sortino ratio. Plot the barplot."""

rolled_sortino = rolling_sortino_portfolio(best_portfolios)

rolled_sortino.plot()
plt.legend()
plt.title('Rolling Sortino Ratio of Portfolios vs. Index')

rolled_sortino.median().plot.bar(color = list('rgbkymc'))
plt.title('Comparison of Portfolios vs. Index by Sortino Ratio')
plt.ylabel('Sortino Ratio')
plt.xlabel('Portfolio')