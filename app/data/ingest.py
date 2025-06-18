# AlphaVantage
from .fetch_alpha_vantage import fetch_stock_data, fetch_crypto_data
from .db import save_to_db  # assuming you have this from earlier

def ingest_stock(symbol="AAPL"):
    df = fetch_stock_data(symbol)
    table_name = symbol.replace("/", "_")
    save_to_db(df, table_name)

    csv_path = f"app/db/{table_name}.csv"
    df.to_csv(csv_path, index=False)

def ingest_crypto(symbol="BTC"):
    df = fetch_crypto_data(symbol)
    table_name = symbol.replace("/", "_")
    save_to_db(df, table_name)

    csv_path = f"app/db/{table_name}.csv"
    df.to_csv(csv_path, index=False)
