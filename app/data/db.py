from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('sqlite:///app/db/market_data.db')

def save_to_db(df, table_name):
    df.to_sql(table_name, engine, if_exists='replace', index=False)

def read_from_db(table_name):
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

