import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 Multi-Stock Super Algo Dashboard")

# === CONFIG ===
LOG_FILE = "multi_stock_log.csv"
TICKERS = ["TSLA", "AAPL", "AMD"]

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(LOG_FILE, names=["Timestamp", "Ticker", "Action", "Qty", "Price", "Sentiment", "PnL"], parse_dates=["Timestamp"])
        df = df.sort_values("Timestamp")
        df["Price"] = pd.to_numeric(df["Price"], errors='coerce')
        df["PnL"] = pd.to_numeric(df["PnL"], errors='coerce').fillna(0)
        df["Sentiment"] = pd.to_numeric(df["Sentiment"], errors='coerce')
        return df
    except:
        return pd.DataFrame(columns=["Timestamp", "Ticker", "Action", "Qty", "Price", "Sentiment", "PnL"])

df = load_data()

if df.empty:
    st.warning("Log file not found or empty.")
else:
    selected_ticker = st.selectbox("Select a Stock to View", TICKERS)
    ticker_df = df[df["Ticker"] == selected_ticker].copy()

    if ticker_df.empty:
        st.info(f"No trades logged for {selected_ticker} yet.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"{selected_ticker} Latest Trade")
            st.dataframe(ticker_df.tail(1).reset_index(drop=True))

            st.subheader("Sentiment History")
            fig, ax = plt.subplots()
            ax.plot(ticker_df["Timestamp"], ticker_df["Sentiment"], marker='o', color='blue')
            ax.set_title("Sentiment Trend")
            ax.set_xlabel("Time")
            ax.set_ylabel("Sentiment")
            ax.grid(True)
            st.pyplot(fig)

        with col2:
            st.subheader(f"{selected_ticker} Trade Log")
            st.dataframe(ticker_df.tail(25).sort_values("Timestamp", ascending=False))

            st.subheader("Cumulative PnL")
            ticker_df["CumulativePnL"] = ticker_df["PnL"].cumsum()
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=ticker_df["Timestamp"], y=ticker_df["CumulativePnL"], name="Cumulative PnL", line=dict(color='green')))
            fig2.update_layout(title=f"{selected_ticker} Cumulative PnL", xaxis_title="Time", yaxis_title="PnL ($)")
            st.plotly_chart(fig2, use_container_width=True)