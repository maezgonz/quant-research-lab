# =========================================================================================
# Prediction Market Trading Bot with Python: From Idea to Deployment
# =========================================================================================
# Important Disclaimer
# =========================================================================================
# Algorithmic trading involves real financial risk.
# This series is educational material.
# It will teach you how to build trading bots, but it does not guarantee profit.
# If you decide to trade with real money, do so with capital you can afford to lose.
# =========================================================================================
# Summary
# =========================================================================================
# Here is what we accomplished in this article:
# - Connected to the Binance API and downloaded historical BTC/USDT candlestick data
# - Cleaned and formatted the data using pandas
# - Learned to filter, slice, and resample time series
# - Calculated simple and logarithmic returns and understood the difference between them
# - Visualized prices, returns, moving averages, and volume
# - Saved data to CSV and HDF5 for future use
# - Wrote a reusable `data_loader.py` script
# The data is ready. The infrastructure is set up. Now we can build strategies.
# =========================================================================================
# Practice Exercise
# =========================================================================================
# Try these on your own:
# 1. Download hourly BTC/USDT candles for the last month. How many rows are in the dataset?
# 2. Calculate log returns and plot their distribution. Does it look normal?
# 3. Resample the hourly data into 4-hour candles. Verify that Open is the first price, High is the maximum, Low is the minimum, and Close is the last price.
# 4. Save the result to both CSV and HDF5. Compare the file sizes.
# 5. Download ETH/USDT (Ethereum) data and plot BTC and ETH prices on the same chart (normalized to 100 at the start of the period).

"""
data_loader.py - Fetch and prepare BTC data from Binance
"""
import pandas as pd
import numpy as np
from binance.client import Client
from pathlib import Path
def fetch_btc_data(interval="1d", lookback="2 years ago UTC"):
    """Fetch historical BTC/USDT candles from Binance."""
    client = Client()
    interval_map = {
        "1d": Client.KLINE_INTERVAL_1DAY,
        "1h": Client.KLINE_INTERVAL_1HOUR,
        "15m": Client.KLINE_INTERVAL_15MINUTE,
        "5m": Client.KLINE_INTERVAL_5MINUTE,
    }
    klines = client.get_historical_klines(
        symbol="BTCUSDT",
        interval=interval_map.get(interval, interval),
        start_str=lookback
    )
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ]
    df = pd.DataFrame(klines, columns=columns)
    # Convert types
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df.set_index("open_time", inplace=True)
    df.index.name = "date"
    df = df[["open", "high", "low", "close", "volume"]]
    return df
def add_returns(df):
    """Add simple and logarithmic returns."""
    df["simple_return"] = df["close"].pct_change()
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df["cumulative_return"] = df["log_return"].cumsum().apply(np.exp) - 1
    return df
def save_data(df, name="btc_daily"):
    """Save data to CSV and HDF5."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    df.to_csv(data_dir / f"{name}.csv")
    df.to_hdf(data_dir / f"{name}.h5", key=name, mode="w")
    print(f"Data saved: {len(df)} records")
if __name__ == "__main__":
    # Fetch daily data
    df = fetch_btc_data(interval="1d", lookback="2 years ago UTC")
    df = add_returns(df)
    save_data(df, name="btc_daily")
    print(f"\nPeriod: {df.index[0].date()} - {df.index[-1].date()}")
    print(f"Total return: {df['cumulative_return'].iloc[-1]:.2%}")
    print(df.tail())

#Save this script as `data_loader.py` in your project root. In the following articles, we will import functions from it:
from data_loader import fetch_btc_data, add_returns
