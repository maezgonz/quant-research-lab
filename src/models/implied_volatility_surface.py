#Build an implied volatility surface with Python
#In today’s newsletter, I’m going to show you how to build an implied volatility surface using Python.
#A volatility surface plots the level of implied volatility in 3D space. The days to expiration are on the X-axis, the strike price is on the Y-axis, and implied volatility is on the Z-axis.
#Implied volatility is the market’s expectations of volatility over the life of an option. To find implied volatility you need three things: the market price of the option, a pricing model, and a root finder. You can then find the volatility that sets the price from the model equal to the price of the market with the root finder. "The volatility implied by the market." The volatility surface is found by repeating this for all options and plotting the results.
#You can use the implied volatility from Yahoo Finance. In practice, traders calculate it themselves. You can too with The 46-Page Ultimate Guide to Pricing Options and Implied Volatility With Python.
#Pricing models assume volatility is the same for all strike prices and maturities. Volatility surfaces show this assumption is not true. Volatility has skew (volatility is different across strike prices) and a term structure (volatility is different across maturities). Quants use volatility surfaces to help calibrate models and price OTC derivatives that don’t trade on exchanges.
#Volatility surfaces prove the models wrong.
#When you value an option, the variables in the model (e.g. stock price, time to expiration) are known except volatility, which is an estimate. If models were completely correct, the volatility surface across strike prices and maturities would be flat. In practice. This is not the case as you’ll see.
#By the end of this issue, you will know how to:

#Get live options data
#Analyze volatility skew
#Analyze volatility structure
#Build an implied volatility surface

#Step 1: Get live options data
#Start by importing the libraries you need. I use yfinance to get options data for free.

import numpy as np
import pandas as pd
import yfinance as yf
import datetime as dt

import matplotlib.pyplot as plt

def option_chains(ticker):
    """
    """
    asset = yf.Ticker(ticker)
    expirations = asset.options
    
    chains = pd.DataFrame()
    
    for expiration in expirations:
        # tuple of two dataframes
        opt = asset.option_chain(expiration)
        
        calls = opt.calls
        calls['optionType'] = "call"
        
        puts = opt.puts
        puts['optionType'] = "put"
        
        chain = pd.concat([calls, puts])
        chain['expiration'] = pd.to_datetime(expiration) + pd.DateOffset(hours=23, minutes=59, seconds=59)
        
        chains = pd.concat([chains, chain])
    
    chains["daysToExpiration"] = (chains.expiration - dt.datetime.today()).dt.days + 1
    
    return chains
#Step 2: Analyze skew and term structure
#Next, get the options data for a stock. I use SPY, the ETF that tracks the S&P 500 index. You can use any stock or ETF that has options traded on it.

options = option_chains("SPY")

calls = options[options["optionType"] == "call"]

#Next, pick an expiration so you can plot the volatility skew.
# print the expirations
set(calls.expiration)

# select an expiration to plot
calls_at_expiry = calls[calls["expiration"] == "2023-01-20 23:59:59"]

# filter out low vols
filtered_calls_at_expiry = calls_at_expiry[calls_at_expiry.impliedVolatility >= 0.001]

# set the strike as the index so pandas plots nicely
filtered_calls_at_expiry[["strike", "impliedVolatility"]].set_index("strike").plot(
    title="Implied Volatility Skew", figsize=(7, 4)
)

#Next, build a volatility term structure. Pick a strike price to plot by expiration.
# select an expiration to plot
calls_at_strike = options[options["strike"] == 400.0]

# filter out low vols
filtered_calls_at_strike = calls_at_strike[calls_at_strike.impliedVolatility >= 0.001]

# set the strike as the index so pandas plots nicely
filtered_calls_at_strike[["expiration", "impliedVolatility"]].set_index("expiration").plot(
    title="Implied Volatility Term Structure", figsize=(7, 4)
)

#Step 3: Plot a volatility surface
#By putting both charts together, you get the volatility surface. In derivatives pricing and trading, volatility surfaces are very important. Quants use the surface to price and trade other more exotic derivatives and look for market mispricings. Volatility surfaces are also used to determine profit and loss by “marking trades to model.”

# pivot the dataframe
surface = (
    calls[['daysToExpiration', 'strike', 'impliedVolatility']]
    .pivot_table(values='impliedVolatility', index='strike', columns='daysToExpiration')
    .dropna()
)

# create the figure object
fig = plt.figure(figsize=(10, 8))

# add the subplot with projection argument
ax = fig.add_subplot(111, projection='3d')

# get the 1d values from the pivoted dataframe
x, y, z = surface.columns.values, surface.index.values, surface.values

# return coordinate matrices from coordinate vectors
X, Y = np.meshgrid(x, y)

# set labels
ax.set_xlabel('Days to expiration')
ax.set_ylabel('Strike price')
ax.set_zlabel('Implied volatility')
ax.set_title('Call implied volatility surface')

# plot
ax.plot_surface(X, Y, z)