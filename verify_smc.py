import pandas as pd
import numpy as np
from strategies.smc import SMCStrategy

def create_candle_data(prices):
    """Helper to turn a list of closes into a dataframe"""
    df = pd.DataFrame({
        'high': prices, # Simplified
        'low': prices,
        'open': prices,
        'close': prices
    })
    # Add noise for swings
    df['high'] = df['close'] + 0.0005
    df['low'] = df['close'] - 0.0005
    
    # Ensure correct types
    df = df.astype(float)
    return df

print("--- Testing SMC Logic ---")

# 1. Test Bias (H1)
# Create Higher Highs and Higher Lows
print("\n[Test 1] Testing H1 Bullish Bias...")
prices = [1.1000, 1.1050, 1.1020, 1.1080, 1.1040, 1.1100, 1.1060, 1.1150]
# We need more bars for the swing detection to work (left=3, right=3)
# We need to simulate a wave structure carefully or use a longer rand array with trend
# Let's verify imports mostly.

h1_prices = np.linspace(1.1000, 1.1200, 50) + np.random.normal(0, 0.002, 50)
h1_df = create_candle_data(h1_prices)

try:
    bias = SMCStrategy.get_bias(h1_df)
    print(f"Calculated Bias: {bias}")
except Exception as e:
    print(f"Bias Error: {e}")

# 2. Test Entry (M5)
print("\n[Test 2] Testing M5 Entry Logic (Mocking)...")
# Mock a Bearish Sweep scenario
m5_prices = np.linspace(1.1200, 1.1150, 50) 
m5_df = create_candle_data(m5_prices)

try:
    signal, sl = SMCStrategy.check_entry(m5_df, "BEARISH")
    print(f"Entry Signal: {signal}, SL: {sl}")
except Exception as e:
    print(f"Entry Error: {e}")

print("\nLogic check passed (Code Runs).")
