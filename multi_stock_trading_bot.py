import alpaca_trade_api as tradeapi
import pandas as pd
import ta
import time
import schedule
import pytz
import logging
from datetime import datetime, timedelta
import xgboost as xgb
from social_sentiment import get_combined_sentiment

# === CONFIG ===
API_KEY = 'PKDAN38C2OGK4BEDU1WN'
SECRET_KEY = 'T2Aa7aV8JPhnFa3RBRvrjfgdNTkk6bAcqIut5ioK'
BASE_URL = 'https://paper-api.alpaca.markets'
TICKERS = ['TSLA', 'AAPL', 'AMD']
MARKET_SYMBOL = 'SPY'
TIMEFRAME = '1Min'
WINDOW = 30
CASH_BUFFER = 0.1
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
COOLDOWN_MINUTES = 5
MAX_TRADES_PER_DAY = 10

# === SETUP ===
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
logging.basicConfig(filename='multi_stock_log.csv', level=logging.INFO, format='%(asctime)s,%(message)s')
models = {ticker: xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss') for ticker in TICKERS}
positions = {}
last_trade_time = {ticker: None for ticker in TICKERS}
trade_count_today = {ticker: 0 for ticker in TICKERS}
cumulative_pnl = {ticker: 0 for ticker in TICKERS}

# === FUNCTIONS ===
def get_data(symbol, limit=WINDOW):
    barset = api.get_bars(symbol, TIMEFRAME, limit=limit).df
    df = barset[barset['symbol'] == symbol].copy()
    df['returns'] = df['close'].pct_change()
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['sma_fast'] = ta.trend.SMAIndicator(df['close'], window=5).sma_indicator()
    df['sma_slow'] = ta.trend.SMAIndicator(df['close'], window=15).sma_indicator()
    df['volatility'] = df['returns'].rolling(window=5).std()
    df['volume_spike'] = df['volume'] / df['volume'].rolling(window=10).mean()
    df.dropna(inplace=True)
    return df

def is_market_open():
    now = datetime.now(pytz.timezone('US/Eastern'))
    return now.weekday() < 5 and ((now.hour == 9 and now.minute >= 30) or (10 <= now.hour < 16))

def train_model(df, market_df, sentiment_score, ticker):
    df['future_return'] = df['returns'].shift(-1)
    df['target'] = (df['future_return'] > 0).astype(int)
    df['spy_return'] = market_df['close'].pct_change().reindex(df.index).fillna(0)
    df['sentiment'] = sentiment_score
    features = ['rsi', 'returns', 'sma_fast', 'sma_slow', 'volatility', 'volume_spike', 'spy_return', 'sentiment']
    df.dropna(inplace=True)
    X = df[features]
    y = df['target']
    models[ticker].fit(X, y)
    return df

def predict_signal(df, market_df, sentiment_score, ticker):
    latest = df.iloc[-1:]
    latest['spy_return'] = market_df['close'].pct_change().iloc[-1]
    latest['sentiment'] = sentiment_score
    features = ['rsi', 'returns', 'sma_fast', 'sma_slow', 'volatility', 'volume_spike', 'spy_return', 'sentiment']
    return models[ticker].predict(latest[features])[0]

def trade_logic(ticker):
    if not is_market_open():
        print(f"[{ticker}] Market is closed.")
        return

    if trade_count_today[ticker] >= MAX_TRADES_PER_DAY:
        print(f"[{ticker}] Max trades reached today.")
        return

    now = datetime.now()
    if last_trade_time[ticker] and (now - last_trade_time[ticker]) < timedelta(minutes=COOLDOWN_MINUTES):
        print(f"[{ticker}] In cooldown period.")
        return

    df = get_data(ticker)
    market_df = get_data(MARKET_SYMBOL)
    sentiment_score = get_combined_sentiment()
    if df.empty or market_df.empty:
        print(f"[{ticker}] Data unavailable.")
        return

    train_model(df, market_df, sentiment_score, ticker)
    prediction = predict_signal(df, market_df, sentiment_score, ticker)
    side = 'buy' if prediction == 1 else 'sell'
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {ticker} Prediction: {side.upper()} | Sentiment: {sentiment_score}")

    try:
        position = api.get_position(ticker)
        entry_price = float(position.avg_entry_price)
        qty = int(float(position.qty))
        price = df['close'].iloc[-1]

        if side == 'sell' and position:
            if (price <= entry_price * (1 - STOP_LOSS_PCT)) or (price >= entry_price * (1 + TAKE_PROFIT_PCT)):
                api.submit_order(symbol=ticker, qty=qty, side='sell', type='market', time_in_force='gtc')
                profit = float(position.unrealized_pl)
                cumulative_pnl[ticker] += profit
                trade_count_today[ticker] += 1
                last_trade_time[ticker] = now
                print(f"SELLING {qty} shares of {ticker} | PnL: ${profit:.2f}")
                logging.info(f"{ticker},SELL,{qty},{price},{sentiment_score},{profit:.2f}")
            return
    except:
        position = None

    if side == 'buy' and not position:
        cash = float(api.get_account().cash) * (1 - CASH_BUFFER) / len(TICKERS)
        price = df['close'].iloc[-1]
        qty = int(cash // price)
        if qty > 0:
            api.submit_order(symbol=ticker, qty=qty, side='buy', type='market', time_in_force='gtc')
            trade_count_today[ticker] += 1
            last_trade_time[ticker] = now
            print(f"BUYING {qty} shares of {ticker}")
            logging.info(f"{ticker},BUY,{qty},{price},{sentiment_score},0")
        else:
            print(f"[{ticker}] Not enough cash.")
    else:
        print(f"[{ticker}] No action taken.")

# === SCHEDULE TASKS ===
for ticker in TICKERS:
    schedule.every(1).minutes.do(lambda t=ticker: trade_logic(t))

print("🚀 Multi-Stock Super Algo running for:", ", ".join(TICKERS))
while True:
    schedule.run_pending()
    time.sleep(1)
