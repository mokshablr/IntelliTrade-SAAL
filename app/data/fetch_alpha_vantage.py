import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
alphavantage_api_key = os.getenv("ALPHAVANTAGE_API_KEY")

def fetch_stock_data(symbol="AAPL"):
    """Fetches the latest 100 days of daily OHLCV data using Alpha Vantage."""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": alphavantage_api_key
    }

    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise RuntimeError(f"Alpha Vantage API error {response.status_code}: {response.text}")

    data = response.json()
    #print(data)  # Remove or comment this in production

    if "Time Series (Daily)" not in data:
        raise ValueError(f"No data found for symbol '{symbol}'. API message: {data.get('Note') or data.get('Error Message') or data}")

    raw = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(raw, orient="index")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    }).astype(float)

    df = df.reset_index().rename(columns={"index": "date"})

    # Sleep to respect API rate limits (5 requests/min)
    time.sleep(12)

    return df


def fetch_crypto_data(symbol="BTC"):
    """Fetches the latest daily OHLCV data for a cryptocurrency from Alpha Vantage."""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "DIGITAL_CURRENCY_DAILY",
        "symbol": symbol,
        "market": "USD",
        "apikey": alphavantage_api_key
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise RuntimeError(f"Alpha Vantage API error {response.status_code}: {response.text}")

    data = response.json()
    
    if "Time Series (Digital Currency Daily)" not in data:
        raise ValueError(f"No data found for symbol '{symbol}'. API message: {data.get('Note') or data.get('Error Message') or data}")

    raw = data["Time Series (Digital Currency Daily)"]

    df = pd.DataFrame.from_dict(raw, orient="index")

    # Rename columns to simplified names and convert to float
    df = df.rename(columns={
        "1a. open (USD)": "open",
        "1. open": "open",
        "2a. high (USD)": "high",
        "2. high": "high",
        "3a. low (USD)": "low",
        "3. low": "low",
        "4a. close (USD)": "close",
        "4. close": "close",
        "5. volume": "volume",
        "6. market cap (USD)": "market_cap"
    }).astype(float)

    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    df = df.reset_index().rename(columns={"index": "date"})

    # Sleep to respect API rate limits (5 calls per minute)
    time.sleep(12)

    return df

if __name__ == "__main__":
    print(f"API KEY: {'SET' if alphavantage_api_key else 'NOT SET'}")
    # df = fetch_stock_data("AAPL")
    # print(df.head())
    df = fetch_crypto_data("BTC")
    print(df.head())

