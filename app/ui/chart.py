import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()

@st.cache_data
def load_csv_data(symbol, interval):
    filename = f"db/{symbol}_{interval}.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename, parse_dates=["timestamp"])
        return df
    else:
        st.warning("CSV file not found.")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_sqlite_data(symbol, asset_type, interval):
    conn = sqlite3.connect("../db/market_data.db")
    query = f"""
        SELECT * FROM candles 
        WHERE symbol='{symbol}' AND type='{asset_type}' AND interval='{interval}'
        ORDER BY timestamp"""
    try:
        df = pd.read_sql_query(query, conn, parse_dates=["timestamp"])
    except Exception as e:
        st.warning(f"Error: {e}")
        df = pd.DataFrame()
    conn.close()
    return df

# freshness check
def is_data_stale(df: pd.DataFrame) -> bool:
    if df.empty:
        return True
    latest_ts = df["timestamp"].max()
    return latest_ts < datetime.utcnow() - timedelta(days=1) # check if data is more than a day old

def ingest_data(symbol, asset_type, interval):
    base_url = os.getenv("API_BASE_URL")
    endpoint = "/ingest-crypto" if asset_type == "crypto" else "/ingest-stock"
    try:
        response = requests.get(f"{base_url}{endpoint}", json={"symbol": symbol, "interval": interval})
        if response.status_code != 200:
            st.error(f"Ingestion failed: {response.status_code} {response.text}")
        else:
            st.success("Data ingested successfully.")
    except Exception as e:
        st.error(f"Failed to contact ingestion service: {e}")

# --- Main render function ---
def render():
    # Layout for filters at the top
    st.subheader("Chart Settings")
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        asset_type = st.selectbox("Asset Type", ["crypto", "stock"])

    with col2:
        default_symbol = "BTC" if asset_type == "crypto" else "TSLA"
        symbol = st.text_input("Search Symbol", default_symbol)

    with col3:
        if asset_type == "crypto":
            interval = st.selectbox("Interval", ["daily", "weekly", "monthly"])
        else:
            interval = st.selectbox("Interval", ["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"])

    # Load data
    df = load_sqlite_data(symbol.upper(), asset_type, interval)

    if is_data_stale(df):
        loading_msg = st.empty()

        # Show loading message
        loading_msg.info("Data is missing or outdated. Fetching fresh data...")

        # st.info("Data is missing or outdated. Fetching fresh data...")
        ingest_data(symbol, asset_type, interval)
        st.cache_data.clear()  # Clear cache after ingestion
        loading_msg.empty()
        df = load_sqlite_data(symbol, asset_type, interval)

    # Display chart if data is available
    if not df.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"]
        )])

        fig.update_layout(
            title=f"{symbol.upper()} - {interval}",
            xaxis_rangeslider_visible=False,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected options.")

print(os.getenv("API_BASE_URL"))
