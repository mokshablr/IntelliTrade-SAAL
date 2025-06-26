from sqlalchemy import create_engine
import pandas as pd
import sqlite3

engine = create_engine('sqlite:///app/db/market_data.db')

# To fetch missing data only, not used yet
def get_latest_timestamp(symbol: str, interval: str, db_path="app/db/market_data.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(timestamp)
        FROM candles
        WHERE symbol = ? AND interval = ?
    """, (symbol, interval))
    result = cursor.fetchone()[0]
    conn.close()
    return pd.to_datetime(result) if result else None


def save_to_db(df):
    conn = sqlite3.connect("app/db/market_data.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            symbol TEXT NOT NULL,
            type TEXT,
            interval TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (symbol, interval, timestamp)
        )
    """)

    # Insert row-by-row with duplicate protection
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO candles (symbol, type, interval, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row["symbol"]),
                str(row["type"]),
                str(row["interval"]),
                str(row["timestamp"]),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                int(row["volume"])
            ))
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()

def read_from_db(table_name):
    return pd.read_sql(f"SELECT * FROM candles where symbol='{table_name}'", engine)
