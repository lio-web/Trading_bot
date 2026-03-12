import argparse
import config
from utils.mt5_interface import MT5Interface
import MetaTrader5 as mt5

def main():
    parser = argparse.ArgumentParser(description='Place a manual trade.')
    parser.add_argument('symbol', type=str, help='Symbol to trade (e.g., CHFJPY)')
    parser.add_argument('direction', type=str, choices=['BUY', 'SELL'], help='Direction (BUY or SELL)')
    parser.add_argument('--lots', type=float, default=0.01, help='Volume in lots')
    parser.add_argument('--sl', type=float, default=0.0, help='Stop Loss Price')
    parser.add_argument('--tp', type=float, default=0.0, help='Take Profit Price')

    args = parser.parse_args()

    print(f"Initializing MT5 for {args.direction} on {args.symbol}...")
    interface = MT5Interface(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER)
    if not interface.startup():
        print("Failed to start MT5.")
        return

    print("Placing order...")
    result = interface.place_order(args.symbol, args.direction, args.lots, args.sl, args.tp)
    
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"SUCCESS: Order placed! {result}")
    else:
        print(f"FAILED: {result}")
        if result:
            print(f"Retcode: {result.retcode}")
            print(f"Comment: {result.comment}")

    interface.shutdown()

if __name__ == "__main__":
    main()
