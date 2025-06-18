# Yfinance
# from .fetch_yfinance import fetch_stock_data
# from .db import save_to_db
# import os
#
# def ingest_stock(symbol="AAPL", start="2020-01-01", end="2024-12-31"):
#     df = fetch_stock_data(symbol, start, end)
#     symbol_name = symbol.replace("/", "_")
#     start_name = start.replace("-", "_")
#     end_name = end.replace("-", "_")
#     table_name = f"{symbol_name}-{start_name}-{end_name}"
#     save_to_db(df, table_name=table_name)
#
#     csv_path = f"app/db/{table_name}.csv"
#     df.to_csv(csv_path, index=False)

# AlphaVantage
from .fetch_alpha_vantage import fetch_stock_data
from .db import save_to_db  # assuming you have this from earlier

def ingest_stock(symbol="AAPL"):
    df = fetch_stock_data(symbol)
    table_name = symbol.replace("/", "_")
    save_to_db(df, table_name)

    csv_path = f"app/db/{table_name}.csv"
    df.to_csv(csv_path, index=False)

