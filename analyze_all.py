import config
from utils.mt5_interface import MT5Interface
from strategies.smc import PriceActionStrategy
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_all_pairs():
    print("Connecting to MT5 to scan for opportunities...")
    mt5_client = MT5Interface(
        os.getenv("MT5_LOGIN", config.MT5_LOGIN), 
        os.getenv("MT5_PASSWORD", config.MT5_PASSWORD), 
        os.getenv("MT5_SERVER", config.MT5_SERVER)
    )
    
    if not mt5_client.startup():
        print("Failed to start MT5 interface.")
        return

    # Remove duplicates from pair list
    pairs = list(set(config.PAIR_LIST))
    print(f"\nAnalyzing {len(pairs)} pairs on {config.TIMEFRAME_TREND} / {config.TIMEFRAME_ENTRY} with EXTRA_CONFLUENCE = {getattr(config, 'EXTRA_CONFLUENCE', False)}\n")

    found_trade = False

    for symbol in pairs:
        # Get Data
        trend_data = mt5_client.get_data(symbol, config.TIMEFRAME_TREND, num_candles=200)
        
        if trend_data is None or len(trend_data) == 0:
             print(f"[{symbol}] Failed to fetch data.")
             continue
             
        bias = PriceActionStrategy.get_structure_bias(trend_data)
        
        # We also need ENTRY data
        entry_data = mt5_client.get_data(symbol, config.TIMEFRAME_ENTRY, num_candles=100)
        
        signal, sl_price, strat_name = PriceActionStrategy.check_entry(entry_data, trend_data)
        
        print(f"[{symbol}] H4 Bias: {bias}")
        if signal:
            print(f"  --> ⭐ POTENTIAL TRADE FOUND! Signal: {signal} | Strategy: {strat_name} | SL: {sl_price}")
            found_trade = True
        else:
            print(f"  --> No valid entry signal right now.")
            
    if not found_trade:
        print("\nNo immediate trade setups found based on the strict criteria.")
    else:
        print("\nOpportunities found! 🚀")

    mt5_client.shutdown()

if __name__ == "__main__":
    analyze_all_pairs()
