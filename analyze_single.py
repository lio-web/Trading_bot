import config
from utils.mt5_interface import MT5Interface
from strategies.smc import PriceActionStrategy
import os
from dotenv import load_dotenv

load_dotenv()

def analyze_symbol(symbol_base):
    print(f"\n--- Analyzing {symbol_base} ---")
    mt5_client = MT5Interface(
        os.getenv("MT5_LOGIN", config.MT5_LOGIN), 
        os.getenv("MT5_PASSWORD", config.MT5_PASSWORD), 
        os.getenv("MT5_SERVER", config.MT5_SERVER)
    )
    
    if not mt5_client.startup():
        print("Failed to start MT5 interface.")
        return

    # Check both normal and .m suffix
    symbols_to_try = [symbol_base, symbol_base + ".m"]
    
    for symbol in symbols_to_try:
        print(f"\nTrying symbol: {symbol}")
        # Get Data
        trend_data = mt5_client.get_data(symbol, config.TIMEFRAME_TREND, num_candles=200)
        
        if trend_data is None or len(trend_data) == 0:
             print(f"[{symbol}] Failed to fetch data. Symbol might not exist or suffix is wrong.")
             continue
             
        bias = PriceActionStrategy.get_structure_bias(trend_data)
        
        # We also need ENTRY data
        entry_data = mt5_client.get_data(symbol, config.TIMEFRAME_ENTRY, num_candles=100)
        
        signal, sl_price, strat_name = PriceActionStrategy.check_entry(entry_data, trend_data)
        
        print(f"[{symbol}] H4 Bias: {bias}")
        if signal:
            print(f"  --> ⭐ POTENTIAL TRADE FOUND! Signal: {signal} | Strategy: {strat_name} | SL: {sl_price}")
        else:
            print(f"  --> No valid entry signal right now.")
            
        break # Successfully analyzed, no need to try other suffix

    mt5_client.shutdown()

if __name__ == "__main__":
    analyze_symbol("XAGUSD")
