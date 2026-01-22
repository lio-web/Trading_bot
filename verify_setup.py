import sys
import pandas as pd
import numpy as np

print("Checking imports...")
try:
    import requests
    import pandas_ta as ta
    print("Imports success.")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

from strategies.technical_analysis import TechnicalAnalysis
from utils.notifier import TelegramNotifier
import config

print("\nChecking Telegram Configuration...")
if not config.TELEGRAM_TOKEN or str(config.TELEGRAM_TOKEN).isdigit():
    print(f"WARNING: TELEGRAM_TOKEN '{config.TELEGRAM_TOKEN}' looks invalid. It should be '123456:ABC-DEF...'")
else:
    print("TELEGRAM_TOKEN format looks plausible.")

print("\nTesting Technical Analysis Logic...")
# Create dummy data
dates = pd.date_range(start='2024-01-01', periods=200, freq='15min')
data = {
    'time': dates,
    'open': np.random.rand(200) * 10 + 100,
    'high': np.random.rand(200) * 10 + 110,
    'low': np.random.rand(200) * 10 + 90,
    'close': np.random.rand(200) * 10 + 100,
    'tick_volume': np.random.randint(1, 100, 200),
}
df = pd.DataFrame(data)

try:
    df_calc = TechnicalAnalysis.calculate_indicators(df)
    print("Indicators calculated successfully.")
    # print columns to debug
    print("Columns:", df_calc.columns.tolist())
    
    signal, pattern = TechnicalAnalysis.check_signals(df_calc)
    print(f"Signal check success. Signal: {signal}, Pattern: {pattern}")
except Exception as e:
    print(f"CRITICAL ERROR in TechnicalAnalysis: {e}")
    import traceback
    traceback.print_exc()

print("\nVerification Complete.")
