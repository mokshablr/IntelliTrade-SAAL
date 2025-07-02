import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

BACKTEST_API_URL = f"{API_BASE_URL}/autotest"  # Change this if your backend is hosted elsewhere

def render():
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col1:
        initial_capital = st.number_input("Initial Capital", min_value=1000, value=10000, step=1000)

    with col2:
        ranking_metric = st.selectbox("Ranking Metric", ["sharpe", "sortino", "calmar", "pnl", "max_drawdown"])

    # Fetching from the main chart
    asset_type = st.session_state.get("asset_type")
    symbol = st.session_state.get("symbol")
    interval = st.session_state.get("interval")

    run_backtest = st.button("🚀 Run Backtest")

    # --- App Title ---
    st.title("📈 Strategy Backtester & Visualizer")

    # --- Main Execution ---
    if run_backtest:
        st.markdown(f"### 📥 Running backtest for `{symbol}` on `{interval}` interval...")

        try:
            response = requests.get(BACKTEST_API_URL, json={
                "initial_capital": initial_capital,
                "ranking_metric": ranking_metric,
                "asset_type": asset_type,
                "symbol": symbol,
                "interval": interval
            })

            if response.status_code != 200:
                st.error(f"❌ API Error: {response.status_code}")
                return

            result = response.json()

            if result["status"] != "success":
                st.error("❌ Backtest failed. Please check your inputs.")
                return

            data = result["data"]
            summary = data["summary"]
            top_results = data["top_strategies"]
            best_strategy = data["best_strategy"]

            # --- Display Summary ---
            st.success(f"✅ Data loaded: {summary['data_points']} candles from {summary['from']} to {summary['to']}")

            # --- Table: Top Strategies ---
            st.subheader("🏆 Top 10 Strategies")

            df_table = pd.DataFrame([{
                "Strategy": row["strategy"],
                "Parameters": str(row["parameters"]),
                "PnL ($)": round(row["stats"]["pnl"], 2),
                "PnL (%)": round(row["stats"]["pnl_percent"], 2),
                "Annual Return": round(row["stats"]["annual_return"] * 100, 2),
                "Sharpe Ratio": round(row["stats"]["sharpe_ratio"], 3),
                "Sortino Ratio": round(row["stats"]["sortino_ratio"], 3),
                "Calmar Ratio": round(row["stats"]["calmar_ratio"], 3),
                "Max Drawdown (%)": round(row["stats"]["max_drawdown"] * 100, 2),
                "Volatility": round(row["stats"]["volatility"] * 100, 2),
                "Trades": int(row["stats"]["total_trades"])
            } for row in top_results])

            st.dataframe(df_table)

            best_name = best_strategy["strategy"]
            best_params = best_strategy["parameters"]
            best_stats = best_strategy["stats"]
            trades_list = best_stats.get("trades_list", [])

            st.session_state["trades_list"] = trades_list

            st.subheader(f"📊 Equity Curve for Best Strategy: {best_name} ({best_params})")

            # Convert list of [date, value] pairs to a Series
            equity_data = best_stats["equity_curve"]
            equity_curve = pd.Series(
                [value for date, value in equity_data],
                index=pd.to_datetime([date for date, value in equity_data])
            )

            equity_lookup = dict(zip(
                equity_curve.index.strftime("%Y-%m-%d %H:%M:%S"),
                equity_curve.values
            ))

            buy_x = []
            buy_y = []
            sell_x = []
            sell_y = []

            for trade in trades_list:
                ts = pd.to_datetime(trade["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                equity_val = equity_lookup.get(ts)
                if equity_val is None:
                    continue  # skip if not found (e.g., timestamp mismatch)

                if trade["action"] == "buy":
                    buy_x.append(ts)
                    buy_y.append(equity_val)
                elif trade["action"] == "sell":
                    sell_x.append(ts)
                    sell_y.append(equity_val)



            fig = go.Figure()

            # Main equity curve
            fig.add_trace(go.Scatter(
                x=equity_curve.index,
                y=equity_curve.values,
                mode='lines',
                name='Equity Curve',
                line=dict(color='royalblue')
            ))

            # Buy/Sell marker plotting
            if trades_list:
                fig.add_trace(go.Scatter(
                    x=buy_x,
                    y=buy_y,
                    mode='markers',
                    name='Buy',
                    marker=dict(symbol='triangle-up', size=10, color='green'),
                    hovertemplate='Buy<br>%{x}<br>Price: %{y:.2f}<extra></extra>'
                ))

                fig.add_trace(go.Scatter(
                    x=sell_x,
                    y=sell_y,
                    mode='markers',
                    name='Sell',
                    marker=dict(symbol='triangle-down', size=10, color='red'),
                    hovertemplate='Sell<br>%{x}<br>Price: %{y:.2f}<extra></extra>'
                ))

            fig.update_layout(
                title="Equity Curve with Buy/Sell Markers",
                xaxis_title="Date",
                yaxis_title="Portfolio Value",
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- Metrics ---
            st.subheader("📋 Best Strategy Stats")
            col1, col2, col3 = st.columns(3)
            col1.metric("PnL ($)", f"${best_stats['pnl']:.2f}")
            col1.metric("PnL (%)", f"{best_stats['pnl_percent']}%")
            col2.metric("Sharpe", f"{best_stats['sharpe_ratio']:.2f}")
            col3.metric("Sortino", f"{best_stats['sortino_ratio']:.2f}")
            col1.metric("Calmar", f"{best_stats['calmar_ratio']:.2f}")
            col2.metric("Max Drawdown", f"{best_stats['max_drawdown']:.2%}")
            col3.metric("Win Rate", f"{best_stats['win_rate']:.2%}")
            col1.metric("Annual Return", f"{best_stats['annual_return']:.2%}")
            col2.metric("Volatility", f"{best_stats['volatility']:.2%}")
            col3.metric("Total Trades", f"{int(best_stats['total_trades'])}")

        except Exception as e:
            st.error(f"❌ An error occurred: {e}")

