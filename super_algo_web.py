import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import subprocess
from datetime import datetime

# === CONFIG ===
TICKERS = ['TSLA', 'AAPL', 'AMD']
LOG_FILE = 'multi_stock_log.csv'
BACKTEST_FILE = 'backtest_results.csv'

st.set_page_config(layout="wide")
st.title("🧠 Super Algo Command Center")

# === Sidebar Controls ===
st.sidebar.header("🛠️ Controls")
run_bot = st.sidebar.button("▶️ Start Bot")
stop_bot = st.sidebar.button("⏹️ Stop Bot")
run_backtest = st.sidebar.button("🔁 Run Backtest")
mode_toggle = st.sidebar.radio("Trading Mode", ["Paper", "Live"])
selected_ticker = st.sidebar.selectbox("Select Ticker", TICKERS)

USE_LIVE = mode_toggle == "Live"
st.sidebar.markdown(f"**Mode Active:** {'🔴 LIVE' if USE_LIVE else '🟢 PAPER'}")

# === Actions ===
if run_bot:
    subprocess.Popen(["python3", "multi_stock_trading_bot.py"])
    st.success("Trading bot started.")

if stop_bot:
    subprocess.run(["pkill", "-f", "multi_stock_trading_bot.py"])
    st.warning("Trading bot stopped.")

if run_backtest:
    subprocess.run(["python3", "super_algo_backtest.py"])
    st.success("Backtest completed.")

# === Load Trade Data ===
def load_trades():
    try:
        df = pd.read_csv(LOG_FILE, names=["Timestamp", "Ticker", "Action", "Qty", "Price", "Sentiment", "PnL"], parse_dates=["Timestamp"])
        df = df.sort_values("Timestamp")
        df["Price"] = pd.to_numeric(df["Price"], errors='coerce')
        df["PnL"] = pd.to_numeric(df["PnL"], errors='coerce').fillna(0)
        df["Sentiment"] = pd.to_numeric(df["Sentiment"], errors='coerce')
        return df
    except:
        return pd.DataFrame()

df = load_trades()
ticker_df = df[df['Ticker'] == selected_ticker]

# === Dashboard Layout ===
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"📈 {selected_ticker} Trade History")
    st.dataframe(ticker_df.tail(20))

    st.subheader("📊 Sentiment Trend")
    fig_sent = go.Figure()
    fig_sent.add_trace(go.Scatter(x=ticker_df["Timestamp"], y=ticker_df["Sentiment"], mode='lines+markers', name='Sentiment'))
    fig_sent.update_layout(title="Sentiment Score Over Time", xaxis_title="Time", yaxis_title="Sentiment")
    st.plotly_chart(fig_sent, use_container_width=True)

with col2:
    st.subheader("💰 Cumulative PnL")
    ticker_df["CumulativePnL"] = ticker_df["PnL"].cumsum()
    fig_pnl = go.Figure()
    fig_pnl.add_trace(go.Scatter(x=ticker_df["Timestamp"], y=ticker_df["CumulativePnL"], name="Cumulative PnL", line=dict(color='green')))
    fig_pnl.update_layout(title="PnL Over Time", xaxis_title="Time", yaxis_title="USD")
    st.plotly_chart(fig_pnl, use_container_width=True)

# === Load Backtest Data ===
st.subheader("📂 Backtest Results")
try:
    bt = pd.read_csv(BACKTEST_FILE)
    st.dataframe(bt.tail(20))
    fig_bt = go.Figure()
    fig_bt.add_trace(go.Scatter(x=bt["Timestamp"], y=bt["CumulativePnL"], name="Backtest Curve", line=dict(color='blue')))
    fig_bt.update_layout(title="Backtest Cumulative PnL", xaxis_title="Time", yaxis_title="USD")
    st.plotly_chart(fig_bt, use_container_width=True)
except:
    st.info("Run a backtest to see results here.")