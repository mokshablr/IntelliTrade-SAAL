from .fetch_yfinance import fetch_stock_data
from .db import save_to_db

def ingest_stock(symbol="AAPL", start="2020-01-01", end="2024-12-31"):
    df = fetch_stock_data(symbol, start, end)
    table_name = symbol.replace("/", "_")
    save_to_db(df, table_name=table_name)

    csv_path = f"app/db/{table_name}.csv"
    df.to_csv(csv_path, index=False)

