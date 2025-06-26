import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
alphavantage_api_key = os.getenv("ALPHAVANTAGE_API_KEY")

def fetch_stock_data(symbol="AAPL", interval="daily", outputsize="compact"):
    """
    Fetches OHLCV stock data from Alpha Vantage for a given symbol and interval.

    Parameters:
        symbol (str): Ticker symbol.
        interval (str): One of ["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"].
        outputsize (str): "compact" (latest 100 rows) or "full".
        apikey (str): Your Alpha Vantage API key.

    Returns:
        pd.DataFrame: A DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume'].
    """
    if alphavantage_api_key is None:
        raise ValueError("Alpha Vantage API key is required.")

    base_url = "https://www.alphavantage.co/query"
    params = {
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": alphavantage_api_key
    }

    # Function and time series key based on interval
    if interval in ["1min", "5min", "15min", "30min", "60min"]:
        params["function"] = "TIME_SERIES_INTRADAY"
        params["interval"] = interval
        ts_key = f"Time Series ({interval})"
    elif interval == "daily":
        params["function"] = "TIME_SERIES_DAILY"
        ts_key = "Time Series (Daily)"
    elif interval == "weekly":
        params["function"] = "TIME_SERIES_WEEKLY"
        ts_key = "Weekly Time Series"
    elif interval == "monthly":
        params["function"] = "TIME_SERIES_MONTHLY"
        ts_key = "Monthly Time Series"
    else:
        raise ValueError("Invalid interval. Must be one of: '1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly'.")

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise RuntimeError(f"Alpha Vantage API error {response.status_code}: {response.text}")

    data = response.json()

    if ts_key not in data:
        raise ValueError(f"No data found for symbol '{symbol}'. API message: {data.get('Note') or data.get('Error Message') or data}")

    raw = data[ts_key]
    df = pd.DataFrame.from_dict(raw, orient="index")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    df = df.rename(columns={
        "date": "timestamp",
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    }).astype(float)

    df["symbol"] = symbol
    df["type"] = "stock"
    df["interval"] = interval
    df = df.reset_index().rename(columns={"index": "timestamp"})

    df = df[["symbol", "type", "interval", "timestamp", "open", "high", "low", "close", "volume"]]

    # Sleep to respect API rate limits (5 requests/min)
    time.sleep(12)

    return df


def fetch_crypto_data(symbol="BTC", market="USD", interval="daily"):
    """
    Fetches OHLCV data for a cryptocurrency from Alpha Vantage's free tier.
    
    Parameters:
        symbol (str): The cryptocurrency symbol (e.g., 'BTC').
        market (str): The fiat currency (e.g., 'USD').
        interval (str): 'daily', 'weekly', or 'monthly'
    
    Returns:
        pd.DataFrame: DataFrame with columns [timestamp, open, high, low, close, volume, market_cap]
    """
    # Map interval to Alpha Vantage function
    function_map = {
        "daily": "DIGITAL_CURRENCY_DAILY",
        "weekly": "DIGITAL_CURRENCY_WEEKLY",
        "monthly": "DIGITAL_CURRENCY_MONTHLY"
    }
    
    if interval not in function_map:
        raise ValueError(f"Invalid interval '{interval}'. Must be 'daily', 'weekly', or 'monthly'.")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": function_map[interval],
        "symbol": symbol,
        "market": market,
        "apikey": alphavantage_api_key
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise RuntimeError(f"Alpha Vantage API error {response.status_code}: {response.text}")

    data = response.json()

    time_series_key = {
        "daily": "Time Series (Digital Currency Daily)",
        "weekly": "Time Series (Digital Currency Weekly)",
        "monthly": "Time Series (Digital Currency Monthly)"
    }[interval]

    if time_series_key not in data:
        raise ValueError(f"No data found for symbol '{symbol}' and interval '{interval}'. API message: {data.get('Note') or data.get('Error Message') or data}")

    raw = data[time_series_key]
    df = pd.DataFrame.from_dict(raw, orient="index")

    # Rename columns and convert to float
    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume",
    })

    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    df = df.reset_index().rename(columns={"index": "timestamp"})

    # Add metadata
    df["symbol"] = symbol
    df["type"] = "crypto"
    df["interval"] = interval

    df = df[["symbol", "type", "interval", "timestamp", "open", "high", "low", "close", "volume"]]

    # Respect free API rate limits
    time.sleep(12)

    return df


if __name__ == "__main__":
    print(f"API KEY: {'SET' if alphavantage_api_key else 'NOT SET'}")
    df = fetch_stock_data("TSLA", "1min")
    print(df.head())
    # df = fetch_crypto_data("BTC")
    # print(df.head())

