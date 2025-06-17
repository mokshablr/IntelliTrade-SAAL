import yfinance as yf
import pandas as pd

def fetch_stock_data(symbol="AAPL", start="2020-01-01", end="2024-12-31"):
    df = yf.download(symbol, start=start, end=end)

    if df is None or df.empty:
        raise ValueError(f"No data for {symbol} between {start} and {end}")

    df.reset_index(inplace=True)
    return df
