import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go

@st.cache_data
def load_csv_data():
    df = pd.read_csv("db/BTC.csv", parse_dates=["timestamp"])
    return df

@st.cache_data
def load_sqlite_data():
    conn = sqlite3.connect("../db/market_data.db")
    df = pd.read_sql_query("SELECT * FROM BTC", conn, parse_dates=["date"])
    conn.close()
    return df

def render():
    df = load_sqlite_data()

    fig = go.Figure(data=[go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )])

    fig.update_layout(xaxis_rangeslider_visible=False, height=400)
    st.plotly_chart(fig, use_container_width=True)
