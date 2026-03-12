import time
from datetime import datetime, timezone, timedelta
import config
from utils.mt5_interface import MT5Interface
from strategies.smc import PriceActionStrategy
from utils.notifier import TelegramNotifier
import MetaTrader5 as mt5

def is_in_session():
    """Checks if current UTC hour is within London or NY session"""
    current_hour = datetime.now(timezone.utc).hour
    in_london = config.SESSION_LONDON_START <= current_hour < config.SESSION_LONDON_END
    in_ny = config.SESSION_NY_START <= current_hour < config.SESSION_NY_END
    return in_london or in_ny

def main():
    print("Initializing Price Action Bot (Conservative Mode)...")
    
    mt5_client = MT5Interface(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER)
    notifier = TelegramNotifier(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    
    if not mt5_client.startup(): return

    print(f"Bot Running. Sessions: London ({config.SESSION_LONDON_START}-{config.SESSION_LONDON_END} UTC), NY ({config.SESSION_NY_START}-{config.SESSION_NY_END} UTC)")
    print(f"Cooldown: {config.COOLDOWN_MINUTES} mins. Lot Size: {config.FIXED_LOT_SIZE}")
    notifier.send_message("🤖 Price Action Bot Started (Conservative Filters Active)")

    # Track last trade time per symbol
    last_trade_time = {}

    try:
        while True:
            now_utc = datetime.now(timezone.utc)
            
            # 1. SESSION FILTER
            if not is_in_session():
                print(f"Outside Session (Hour: {now_utc.hour} UTC). Sleeping...")
                time.sleep(300)
                continue

            # 2. DAILY TRADE LIMIT
            if mt5_client.get_open_positions_count() >= config.MAX_TRADES_PER_DAY:
                print("Max trades reached. Waiting...")
                time.sleep(300)
                continue

            for symbol in config.PAIR_LIST:
                # 3. COOLDOWN CHECK
                if symbol in last_trade_time:
                    elapsed = (datetime.now() - last_trade_time[symbol]).total_seconds() / 60
                    if elapsed < config.COOLDOWN_MINUTES:
                        # Silently skip or log debug
                        # print(f"[{symbol}] In Cooldown ({int(elapsed)}/{config.COOLDOWN_MINUTES}m)")
                        continue

                # 4. STRUCTURE ANALYSIS
                trend_data = mt5_client.get_data(symbol, config.TIMEFRAME_TREND, num_candles=200)
                bias = PriceActionStrategy.get_structure_bias(trend_data)
                
                print(f"[{symbol}] Structure: {bias}")
                
                if bias == "NEUTRAL": continue
                    
                # 5. ENTRY SIGNAL
                entry_data = mt5_client.get_data(symbol, config.TIMEFRAME_ENTRY, num_candles=100)
                signal, sl_price, strat_name = PriceActionStrategy.check_entry(entry_data, trend_data)
                
                # Double check open positions FIRST
                current_positions = mt5.positions_get(symbol=symbol)
                
                if current_positions and len(current_positions) > 0:
                    if signal:
                        # We have an open trade on this symbol, and just got a new signal. Is it a reversal?
                        for pos in current_positions:
                            pos_type_str = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
                            
                            # If the new signal completely opposes our current open position, close it to avoid full stop-loss!
                            if (pos_type_str == "BUY" and signal == "SELL") or (pos_type_str == "SELL" and signal == "BUY"):
                                print(f"[{symbol}] EARLY REVERSAL DETECTED! Closing {pos_type_str} position early.")
                                res = mt5_client.close_position(pos)
                                
                                if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                                    msg = f"🚨 CLOSED EARLY: {symbol} (Reversal Signal: {signal})\nClosed {pos_type_str} Position early to secure funds!\nStrategy: {strat_name}"
                                    notifier.send_message(msg)
                                else:
                                    print(f"[{symbol}] Failed to close position early: {res}")
                                    
                    # Whether we closed it or it wasn't a reversal, skip opening brand new trades for this symbol right now
                    continue
                
                if signal:
                    print(f"[{symbol}] Signal: {signal} ({strat_name}) | SL: {sl_price}")
                    
                    # 6. EXECUTION
                    tick = mt5.symbol_info_tick(symbol)
                    entry_price = tick.ask if signal == "BUY" else tick.bid
                    
                    risk_dist = abs(entry_price - sl_price)
                    tp_price = 0.0
                    
                    if signal == "BUY":
                        tp_price = entry_price + (risk_dist * config.MIN_RR)
                    else:
                        tp_price = entry_price - (risk_dist * config.MIN_RR)
                        
                    lots = config.FIXED_LOT_SIZE
                    
                    print(f"[{symbol}] Executing {signal} | Lots: {lots}")
                    result = mt5_client.place_order(symbol, signal, lots, sl_price, tp_price)
                    
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        msg = f"🚀 EXECUTED: {symbol} {signal}\nStrat: {strat_name}\nLots: {lots}\nSL: {sl_price}\nTP: {tp_price}"
                        notifier.send_message(msg)
                        
                        # UPDATE COOLDOWN
                        last_trade_time[symbol] = datetime.now()
                    else:
                        print(f"Trade Failed: {result}")
                        
            print("Cycle check complete. Waiting 60s...")
            time.sleep(60)

    except KeyboardInterrupt:
        print("Stopping...")
        mt5_client.shutdown()

if __name__ == "__main__":
    main()
