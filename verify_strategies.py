import config
from utils.mt5_interface import MT5Interface
from strategies.smc import PriceActionStrategy
import time

def run_verification():
    print("--- Starting Verification ---")
    mt5_client = MT5Interface(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER)
    if not mt5_client.startup():
        print("MT5 Init Failed")
        return

    print("Connected to MT5. Checking signals on historical data (ignoring session time)...")
    
    for symbol in config.PAIR_LIST:
        print(f"\nAnalyzing {symbol}...")
        
        # Get Data
        trend_data = mt5_client.get_data(symbol, config.TIMEFRAME_TREND, num_candles=200)
        entry_data = mt5_client.get_data(symbol, config.TIMEFRAME_ENTRY, num_candles=200)
        
        if trend_data is None or entry_data is None:
            print("Failed to get data.")
            continue
            
        # Check Strategy
        bias = PriceActionStrategy.get_structure_bias(trend_data)
        print(f"Structure ({config.TIMEFRAME_TREND}): {bias}")
        
        signal, sl, strat = PriceActionStrategy.check_entry(entry_data, trend_data)
        
        if signal:
            print(f"SIGNAL FOUND: {signal} @ {entry_data.iloc[-1]['close']}")
            print(f"   Strategy: {strat}")
            print(f"   SL: {sl}")
        else:
            print("   No Signal.")
            
    mt5_client.shutdown()
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    run_verification()
