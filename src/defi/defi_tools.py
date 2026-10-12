import requests
import pandas as pd
from datetime import datetime

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
PCS_BASE = "https://api.pancakeswap.info/api/v2"


def geckoPrice(coin_id: str, vs_currency: str = "usd") -> float:
    url = f"{COINGECKO_BASE}/simple/price"
    params = {"ids": coin_id, "vs_currencies": vs_currency}
    r = requests.get(url, params=params, timeout=15)
    return r.json().get(coin_id, {}).get(vs_currency, 0.0)


def geckoMarkets(coin_id: str) -> list[dict]:
    url = f"{COINGECKO_BASE}/coins/{coin_id}/tickers"
    r = requests.get(url, timeout=15)
    return r.json().get("tickers", [])


def geckoHistorical(coin_id: str, days: int = 30, vs_currency: str = "usd") -> pd.DataFrame:
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days}
    r = requests.get(url, params=params, timeout=15)
    prices = r.json().get("prices", [])
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("date", inplace=True)
    return df


def getProtocols() -> list[dict]:
    url = f"{COINGECKO_BASE}/defi"
    r = requests.get(url, timeout=15)
    return r.json()


def getProtocol(protocol_id: str) -> dict:
    url = f"{COINGECKO_BASE}/defi/{protocol_id}"
    r = requests.get(url, timeout=15)
    return r.json()


def pcsTokens() -> list:
    url = f"{PCS_BASE}/tokens"
    r = requests.get(url, timeout=15)
    return list(r.json().get("data", {}).values())


def pcsTokenInfo(address: str) -> dict:
    url = f"{PCS_BASE}/tokens/{address}"
    r = requests.get(url, timeout=15)
    return r.json().get("data", {})


def pcsPairs() -> list:
    url = f"{PCS_BASE}/pairs"
    r = requests.get(url, timeout=15)
    return list(r.json().get("data", {}).values())


def pcsPairInfo(address: str) -> dict:
    url = f"{PCS_BASE}/pairs/{address}"
    r = requests.get(url, timeout=15)
    return r.json().get("data", {})


def farmSimulate(amount: float, apr: float, days: int = 365) -> dict:
    daily = apr / 365
    for _ in range(days):
        amount *= 1 + daily
    return {"final_value": round(amount, 2), "days": days}


def iloss(price_ratio: float, pool_weight: float = 0.5) -> float:
    k = price_ratio ** pool_weight
    return (2 * k / (1 + k)) - 1


def iloss_simulate(initial_price: float, final_price: float, invested: float, pool_weight: float = 0.5) -> dict:
    ratio = final_price / initial_price
    loss_pct = iloss(ratio, pool_weight)
    hodl_value = invested * ratio
    lp_value = invested * (1 + loss_pct)
    return {
        "hodl": round(hodl_value, 2),
        "lp": round(lp_value, 2),
        "il_pct": round(loss_pct * 100, 2),
    }


def compare(strategy_results: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(strategy_results)


def value_f(x: float) -> float:
    return x
