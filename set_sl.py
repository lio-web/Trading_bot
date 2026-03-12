import argparse
import config
from utils.mt5_interface import MT5Interface
import MetaTrader5 as mt5

def main():
    parser = argparse.ArgumentParser(description='Modify position SL/TP')
    parser.add_argument('ticket', type=int, help='Position Ticket')
    parser.add_argument('sl', type=float, help='Stop Loss Price')
    parser.add_argument('--tp', type=float, default=0.0, help='Take Profit Price')

    args = parser.parse_args()

    mt5_int = MT5Interface(config.MT5_LOGIN, config.MT5_PASSWORD, config.MT5_SERVER)
    if not mt5_int.startup():
        print("Failed to connect.")
        return

    print(f"Modifying Ticket {args.ticket} to SL: {args.sl} TP: {args.tp}...")
    result = mt5_int.modify_position(args.ticket, args.sl, args.tp)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("SUCCESS: Position modified.")
    else:
        print(f"FAILED: {result.comment} ({result.retcode})")

    mt5_int.shutdown()

if __name__ == "__main__":
    main()
