# LIVE TRADING CONFIG MODULE

# ✅ Toggle to switch between paper and live trading
USE_LIVE = False  # Set to True when ready for live trades

if USE_LIVE:
    API_KEY = 'your_live_api_key_here'
    SECRET_KEY = 'your_live_secret_key_here'
    BASE_URL = 'https://api.alpaca.markets'
    MAX_DAILY_LOSS = -50  # More strict for real money
else:
    API_KEY = 'PKDAN38C2OGK4BEDU1WN'
    SECRET_KEY = 'T2Aa7aV8JPhnFa3RBRvrjfgdNTkk6bAcqIut5ioK'
    BASE_URL = 'https://paper-api.alpaca.markets'
    MAX_DAILY_LOSS = -100  # Paper trading limit

# === Example usage inside your bot ===
from datetime import datetime
import pytz

cumulative_pnl = 0

# Inside your trade logic:
if cumulative_pnl <= MAX_DAILY_LOSS:
    print("🚨 Daily loss limit reached. Trading stopped.")
    return

# === Optional: Slack/Email Alert ===
def send_alert(message):
    # Add integration with Slack webhook, Twilio SMS, or SMTP email here
    print(f"ALERT: {message}")

if cumulative_pnl <= MAX_DAILY_LOSS and USE_LIVE:
    send_alert("Super Algo LIVE mode halted: Max daily loss hit.")