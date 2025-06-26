from .fetch_alpha_vantage import fetch_stock_data, fetch_crypto_data
from .db import save_to_db

def ingest_stock(symbol="AAPL", interval="daily", outputsize="compact"):
    df = fetch_stock_data(symbol, interval, outputsize)
    save_to_db(df)

    table_name = symbol.replace("/", "_")
    csv_path = f"app/db/{table_name}.csv"
    df.to_csv(csv_path, index=False)

def ingest_crypto(symbol="BTC", interval="daily"):
    market = "USD"
    df = fetch_crypto_data(symbol, market, interval)

    save_to_db(df)

    table_name = symbol.replace("/", "_")

    csv_path = f"app/db/{table_name}.csv"
    df.to_csv(csv_path, index=False)
