import pandas as pd
import yfinance as yf
import ta
import xgboost as xgb
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# === CONFIG ===
SYMBOL = 'TSLA'
MARKET = 'SPY'
START_DATE = '2023-12-01'
END_DATE = '2023-12-15'
TIMEFRAME = '1m'
WINDOW = 30
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04

# === Download Historical Data ===
def get_data(symbol):
    df = yf.download(symbol, start=START_DATE, end=END_DATE, interval='1m')
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.columns = [col.lower() for col in df.columns]
    df.index.name = 'timestamp'
    return df.dropna()

# === Feature Engineering ===
def prepare_features(df, market_df):
    df['returns'] = df['close'].pct_change()
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['sma_fast'] = ta.trend.SMAIndicator(df['close'], window=5).sma_indicator()
    df['sma_slow'] = ta.trend.SMAIndicator(df['close'], window=15).sma_indicator()
    df['volatility'] = df['returns'].rolling(window=5).std()
    df['volume_spike'] = df['volume'] / df['volume'].rolling(window=10).mean()
    df['spy_return'] = market_df['close'].pct_change().reindex(df.index).fillna(0)
    df['future_return'] = df['returns'].shift(-1)
    df['target'] = (df['future_return'] > 0).astype(int)
    df.dropna(inplace=True)
    return df

# === Backtest Logic ===
def backtest(df):
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    X = df[['rsi', 'returns', 'sma_fast', 'sma_slow', 'volatility', 'volume_spike', 'spy_return']]
    y = df['target']
    model.fit(X, y)

    df['prediction'] = model.predict(X)
    position = None
    entry_price = 0
    trades = []
    pnl = 0

    for i in range(len(df)):
        row = df.iloc[i]
        price = row['close']

        if position == 'long':
            if price <= entry_price * (1 - STOP_LOSS_PCT) or price >= entry_price * (1 + TAKE_PROFIT_PCT):
                profit = (price - entry_price)
                pnl += profit
                trades.append((row.name, 'SELL', price, profit))
                position = None

        if position is None and row['prediction'] == 1:
            entry_price = price
            trades.append((row.name, 'BUY', price, 0))
            position = 'long'

    return trades, pnl

# === Run Backtest ===
print("Downloading historical data...")
df_stock = get_data(SYMBOL)
df_market = get_data(MARKET)
df = prepare_features(df_stock, df_market)
print("Running backtest...")
trades, total_pnl = backtest(df)

# === Results ===
print(f"Total trades: {len(trades)}")
print(f"Total PnL: ${total_pnl:.2f}")

# Save trades
results = pd.DataFrame(trades, columns=['Timestamp', 'Action', 'Price', 'PnL'])
results['CumulativePnL'] = results['PnL'].cumsum()
results.to_csv("backtest_results.csv", index=False)

# Plot PnL
plt.figure(figsize=(12, 6))
plt.plot(results['Timestamp'], results['CumulativePnL'], label='Cumulative PnL', color='green')
plt.title(f"Backtest Results for {SYMBOL}")
plt.xlabel("Time")
plt.ylabel("Cumulative PnL ($)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
