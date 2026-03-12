import config
from utils.mt5_interface import MT5Interface
import MetaTrader5 as mt5

def check():
    mt5_int = MT5Interface(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER)
    if not mt5_int.startup():
        return

    positions = mt5.positions_get(symbol="CHFJPY")
    if positions:
        for pos in positions:
            print(f"Ticket: {pos.ticket} | Symbol: {pos.symbol} | Type: {'BUY' if pos.type==0 else 'SELL'} | Vol: {pos.volume} | Open: {pos.price_open} | Current SL: {pos.sl}")
    else:
        print("No open positions for CHFJPY")
    
    mt5_int.shutdown()

if __name__ == "__main__":
    check()
