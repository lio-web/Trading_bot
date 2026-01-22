import os
from dotenv import load_dotenv

load_dotenv()

# MT5 Login Credentials
MT5_LOGIN = 5045134125
MT5_PASSWORD = "JuGx!5Kd"
MT5_SERVER = "MetaQuotes-Demo"

# Trading Settings
SYMBOLS = ["CHFJPY"] # Add your symbols here
TIMEFRAME = "M15"  # 15 Minute candles
VOLUME = 0.01  # Lot size
DEVIATION = 20  # Max price deviation in points
MAGIC_NUMBER = 123456

# Indicator Settings
RSI_PERIOD = 14
SMA_PERIOD = 50
BB_PERIOD = 20
BB_STD_DEV = 2.0
STOCH_K = 14
STOCH_D = 3
STOCH_SLOW = 3

# Telegram Notification Settings
TELEGRAM_TOKEN = "8531428244:AAFvnYRIeoD1rzd5yr-uceBDIBk9CZ4REKI"  # Get from @BotFather
TELEGRAM_CHAT_ID = "8437636808"  # Get from @userinfobot
