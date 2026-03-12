import config
from utils.mt5_interface import MT5Interface
from strategies.smc import SMCStrategy
import pandas as pd

def analyze():
    print("Connecting to MT5...")
    mt5 = MT5Interface(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER)
    if not mt5.startup():
        print("Failed to connect.")
        return

    symbol = "CHFJPY"
    print(f"Analyzing {symbol}...")

    # Get H1 Data for Bias
    h1_data = mt5.get_data(symbol, config.TIMEFRAME_BIAS, num_candles=200)
    bias = SMCStrategy.get_bias(h1_data)
    print(f"H1 Bias: {bias}")

    # Get M5 Data for Signal
    m5_data = mt5.get_data(symbol, config.TIMEFRAME_ENTRY, num_candles=200)
    signal, sl = SMCStrategy.check_entry(m5_data, bias)
    
    print(f"Entry Signal: {signal}")
    print(f"Suggested SL: {sl}")

    mt5.shutdown()

if __name__ == "__main__":
    analyze()
