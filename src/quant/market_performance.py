################# Stock Market Performance Analysis using Python ##############

import pandas as pd
import yfinance as yf
from datetime import datetime

start_date = datetime.now() - pd.DateOffset(months=12)
end_date = datetime.now()

tickers = ['GGAL', 'PAM', 'YPF', 'BMA']

df_list = []

for ticker in tickers:
    data = yf.download(ticker, start=start_date, end=end_date)
    df_list.append(data)

df = pd.concat(df_list, keys=tickers, names=['Ticker', 'Date'])
print(df.head())

df = df.reset_index()
print(df.head())


import plotly.express as px
fig = px.line(df, x='Date', 
              y='Close', 
              color='Ticker', 
              title="Stock Market Performance for the Last 3 Months")
fig.show()


fig = px.area(df, x='Date', y='Close', color='Ticker',
              facet_col='Ticker',
              labels={'Date':'Date', 'Close':'Closing Price', 'Ticker':'Company'},
              title='Stock Prices for Banco Galicia, YPF, Pampa Energia and Banco Macro')
fig.show()

df['MA10'] = df.groupby('Ticker')['Close'].rolling(window=10).mean().reset_index(0, drop=True)
df['MA20'] = df.groupby('Ticker')['Close'].rolling(window=20).mean().reset_index(0, drop=True)

for ticker, group in df.groupby('Ticker'):
    print(f'Moving Averages for {ticker}')
    print(group[['MA10', 'MA20']])
    
for ticker, group in df.groupby('Ticker'):
    fig = px.line(group, x='Date', y=['Close', 'MA10', 'MA20'], 
                  title=f"{ticker} Moving Averages")
    fig.show()
    
df['Volatility'] = df.groupby('Ticker')['Close'].pct_change().rolling(window=10).std().reset_index(0, drop=True)
fig = px.line(df, x='Date', y='Volatility', 
              color='Ticker', 
              title='Volatility of All Companies')
fig.show()

# create a DataFrame with the stock prices of Apple and Microsoft
apple = df.loc[df['Ticker'] == 'GGAL', ['Date', 'Close']].rename(columns={'Close': 'GGAL'})
microsoft = df.loc[df['Ticker'] == 'YPF', ['Date', 'Close']].rename(columns={'Close': 'YPF'})
df_corr = pd.merge(apple, microsoft, on='Date')

# create a scatter plot to visualize the correlation
fig = px.scatter(df_corr, x='GGAL', y='YPF', 
                 trendline='ols', 
                 title='Correlation between Banco Galicia and YPF')
fig.show()

