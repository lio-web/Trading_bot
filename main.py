import time
import config
from strategies.technical_analysis import TechnicalAnalysis
from utils.mt5_interface import MT5Interface
from utils.notifier import TelegramNotifier
import MetaTrader5 as mt5

def main():
    print("Starting Trading Bot...")
    
    # Initialize Notifier
    notifier = TelegramNotifier(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    notifier.send_message("🤖 Trading Bot Started!")

    # Initialize MT5 Interface
    mt5_client = MT5Interface(
        login=config.MT5_LOGIN,
        password=config.MT5_PASSWORD,
        server=config.MT5_SERVER
    )
    
    if not mt5_client.startup():
        print("Failed to start MT5 Client")
        return

    print("Bot is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            for symbol in config.SYMBOLS:
                # 1. Fetch Data
                df = mt5_client.get_data(symbol, config.TIMEFRAME)
                
                if df is not None:
                    # 2. Calculate Indicators
                    df = TechnicalAnalysis.calculate_indicators(df)
                    
                    # 3. Check for Signals
                    signal, pattern = TechnicalAnalysis.check_signals(df) # Now returns tuple
                    
                    if signal:
                        print(f"[{symbol}] Signal Detected: {signal} (Pattern: {pattern})")
                        
                        # 4. Check for existing positions
                        positions = mt5_client.get_open_positions(symbol)
                        if positions and len(positions) > 0:
                            print(f"[{symbol}] Position already open. Skipping trade.")
                            continue

                        # 5. Execute Trade
                        symbol_info = mt5_client.get_symbol_info(symbol)
                        if symbol_info is None:
                            print(f"[{symbol}] Failed to get symbol info")
                            continue
                            
                        point = symbol_info.point
                        tick = mt5.symbol_info_tick(symbol)
                        if not tick:
                            print(f"[{symbol}] Failed to get tick data")
                            continue
                            
                        current_price = tick.ask if signal == "BUY" else tick.bid
                        
                        sl_dist = 100 * point
                        tp_dist = 200 * point
                        
                        sl = current_price - sl_dist if signal == "BUY" else current_price + sl_dist
                        # tp = current_price + tp_dist if signal == "BUY" else current_price - tp_dist
                        tp = 0.0 # No Take Profit (Manual Close)
                        
                        result = mt5_client.place_order(
                            symbol=symbol,
                            order_type=signal,
                            lots=config.VOLUME,
                            sl=sl,
                            tp=tp
                        )

                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            msg = f"🚀 Order Placed!\nType: {signal}\nSymbol: {symbol}\nPrice: {result.price}\nVolume: {result.volume}\nPattern: {pattern}"
                            notifier.send_message(msg)
                            print(msg)
                        else:
                            err_msg = f"[{symbol}] Order failed: {result}"
                            print(err_msg)
                            notifier.send_message(f"⚠️ {err_msg}")
                    else:
                        # Detailed Logging for debuggin
                        latest = df.iloc[-1]
                        rsi_val = latest['RSI']
                        try:
                            stoch_k_col = [c for c in df.columns if c.startswith('STOCHk')][0]
                            stoch_k_val = latest[stoch_k_col]
                        except:
                            stoch_k_val = 0.0
                            
                        pattern_txt = f" | Pattern: {pattern}" if pattern else ""
                        print(f"[{symbol}] No Signal. Close: {latest['close']:.5f} | RSI: {rsi_val:.2f} | Stoch: {stoch_k_val:.2f}{pattern_txt}")
                else:
                    print(f"[{symbol}] Failed to fetch data")
                    
            # Sleep to match timeframe or poll interval
            print("Waiting 60 seconds...")
            time.sleep(60) # Check every minute
            
    except KeyboardInterrupt:
        print("Stopping Bot...")
        notifier.send_message("🛑 Trading Bot Stopped.")
    finally:
        mt5_client.shutdown()

if __name__ == "__main__":
    main()
