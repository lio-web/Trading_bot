import os
from dotenv import load_dotenv

load_dotenv()

# --- MT5 CREDENTIALS ---
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "5045134125"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "JuGx!5Kd")
MT5_SERVER = os.getenv("MT5_SERVER", "MetaQuotes-Demo")

# --- GLOBAL PARAMETERS ---
# Real accounts on this broker prefix symbols with .m
PAIR_LIST = ["EURUSD.m", "GBPUSD.m", "USDJPY.m", "CHFJPY.m", "NZDJPY.m", "GBPJPY.m"]

# --- TIMEFRAMES ---
TIMEFRAME_TREND = "H4"   # Structure/Bias
TIMEFRAME_ENTRY = "M15"  # Entry Signals
TIMEFRAME_BIAS = "H1"    # Keeping for compatibility

# --- STRATEGY SETTINGS ---
ENABLE_STRATEGY_PINBAR = True
ENABLE_STRATEGY_ENGULFING = True
ENABLE_STRATEGY_INSIDE_BAR = True
ENABLE_STRATEGY_RANGE = True

# --- EXTRA FILTERS (FOR REAL ACCOUNT) ---
EXTRA_CONFLUENCE = True  # If True, requires EMA alignment and Volume confirmation
EMA_FAST = 50
EMA_SLOW = 200

# --- RISK MANAGEMENT ---
USE_FIXED_LOTS = False   # Set to False to use percentage-based risk on your real account
FIXED_LOT_SIZE = 0.01    # Kept very small (micro-lot) just in case you toggle FIXED_LOTS back on

RISK_PER_TRADE = 0.01    # 1% risk per trade of your account balance

# --- TAKE PROFIT SETTINGS ---
# TP is calculated based on Risk:Reward ratio (Distance to Stop Loss)
MIN_RR = 2.0             # 2.0 = TP is 2x the Stop Loss distance

MAX_TRADES_PER_DAY = 3
MAX_SPREAD_POINTS = 20 # points
COOLDOWN_MINUTES = 60  # Wait time between trades on same symbol

# --- SESSION TIMES (UTC) ---
# London: 07:00 - 11:00
SESSION_LONDON_START = 7
SESSION_LONDON_END = 11

# New York: 13:00 - 17:00
SESSION_NY_START = 13
SESSION_NY_END = 17

# --- TELEGRAM ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8531428244:AAFvnYRIeoD1rzd5yr-uceBDIBk9CZ4REKI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8437636808")
