import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta, timezone
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

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Localize if timestamps are naive (i.e., tz is None)
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("America/New_York")

    # Convert to UTC
    df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")

    latest_ts = df["timestamp"].max()

    return latest_ts < datetime.now(timezone.utc) - timedelta(days=1)


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

def get_time_delta(interval):
    if interval == "1min":
        return timedelta(hours=1)
    elif interval == "5min":
        return timedelta(hours=6)
    elif interval == "15min":
        return timedelta(days=1)
    elif interval == "30min":
        return timedelta(days=2)
    elif interval == "60min":
        return timedelta(days=3)
    elif interval == "daily":
        return timedelta(days=30)
    elif interval == "weekly":
        return timedelta(weeks=12)
    elif interval == "monthly":
        return timedelta(weeks=52)
    else:
        return timedelta(days=30)  # fallback to full range

# --- Main render function ---
def render():
    trades_list = st.session_state.get("trades_list", None)

    # --- Chart Settings UI ---
    st.subheader("Chart Settings")
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        asset_type = st.selectbox("Asset Type", ["crypto", "stock"], key="asset_type")

    with col2:
        default_symbol = "BTC" if asset_type == "crypto" else "TSLA"
        symbol = st.text_input("Search Symbol", default_symbol, key="symbol")

    with col3:
        interval_options = ["daily", "weekly", "monthly"] if asset_type == "crypto" else \
                           ["1min", "5min", "15min", "30min", "60min", "daily", "weekly", "monthly"]
        interval = st.selectbox("Interval", interval_options, key="interval", index=2 if asset_type != "crypto" else 0)
    
    # Since changes in input values causes page render. Page render ends up calling ingest API unnecessarily
    ingest_requested = st.button("🔄 Ingest Fresh Data")

    if ingest_requested:
        st.session_state["ingest_requested"] = True

    if "ingest_requested" not in st.session_state:
        st.session_state["ingest_requested"] = False

    asset_type = st.session_state.asset_type
    symbol = st.session_state.symbol
    interval = st.session_state.interval

    # --- Load Data ---
    df = load_sqlite_data(symbol.upper(), asset_type, interval)

    # Ensure timestamp is timezone-aware in Eastern Time (ET)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("America/New_York")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert("America/New_York")

    if is_data_stale(df):
        st.warning("⚠️ Data is stale or missing. Please click '🔄 Ingest Fresh Data' to fetch.")

    if st.session_state["ingest_requested"]:
        with st.spinner("Fetching fresh data..."):
            ingest_data(symbol, asset_type, interval)
            st.cache_data.clear()
            df = load_sqlite_data(symbol, asset_type, interval)
        st.session_state["ingest_requested"] = False  # Reset flag after ingestion

    # Convert the fresh data to ET
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("America/New_York")
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert("America/New_York")

    # --- Chart Rendering ---
    if not df.empty:
        fig = go.Figure()

        # Price candlestick
        fig.add_trace(go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price"
        ))

        # Only plot if trades are from current symbol+interval
        if trades_list:
            df_times = pd.to_datetime(df["timestamp"])
            df_range = (df_times.min(), df_times.max())

            # Filter only trades that fall in this visible range
            eastern = timezone(timedelta(hours=-5))
            def ensure_et(ts):
                dt = pd.to_datetime(ts)
                if dt.tzinfo is None or dt.tz is None:
                    return dt.tz_localize(eastern)
                return dt.tz_convert(eastern)

            trades_filtered = [
                t for t in trades_list
                if ensure_et(df_range[0]) <= ensure_et(t["timestamp"]) <= ensure_et(df_range[1])
            ]

            if trades_filtered:
                buy_x = []
                buy_y = []
                sell_x = []
                sell_y = []

                for t in trades_filtered:
                    ts = pd.to_datetime(t["timestamp"]).tz_localize("America/New_York")
                    price = t["price"]
                    if t["action"] == "buy":
                        buy_x.append(ts)
                        buy_y.append(price)
                    elif t["action"] == "sell":
                        sell_x.append(ts)
                        sell_y.append(price)

                fig.add_trace(go.Scatter(
                    x=buy_x,
                    y=buy_y,
                    mode='markers',
                    name='Buy',
                    marker=dict(symbol='triangle-up', size=10, color='green'),
                    hovertemplate='Buy: %{y:.2f}<br>%{x}<extra></extra>'
                ))

                fig.add_trace(go.Scatter(
                    x=sell_x,
                    y=sell_y,
                    mode='markers',
                    name='Sell',
                    marker=dict(symbol='triangle-down', size=10, color='red'),
                    hovertemplate='Sell: %{y:.2f}<br>%{x}<extra></extra>'
                ))

        # Ensure datetime index
        # df.index = df["timestamp"]
        # df = df.sort_index()
        df.index = pd.to_datetime(df["timestamp"])
        df = df.sort_index()

        # Calculate x-axis range to show latest data based on interval
        end_date = df.index.max()
        start_date = end_date - get_time_delta(interval)

        # Filter for visible range to calculate y-axis limits
        visible_df = df[(df.index >= start_date) & (df.index <= end_date)]

        y_min = visible_df['low'].min()
        y_max = visible_df['high'].max()
        y_padding = (y_max - y_min) * 0.05 if y_max > y_min else 1  # safe padding

        fig.add_trace(go.Scatter(
            x=[start_date, end_date],
            y=[y_min - y_padding, y_max + y_padding],
            mode='lines',
            line=dict(color='rgba(0,0,0,0)'),
            showlegend=False,
            hoverinfo='none',
        ))

        fig.update_layout(
            title=f"{symbol.upper()} - {interval}",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis=dict(
                type="date",
                range=[start_date, end_date],
                rangeslider=dict(visible=True),
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(count=7, label="1w", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
            ),
            yaxis=dict(autorange=True, fixedrange=False,),
            height=500,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected options.")
