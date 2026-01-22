import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time

class MT5Interface:
    def __init__(self, login, password, server):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False

    def startup(self):
        if not mt5.initialize():
            print(f"initialize() failed, error code = {mt5.last_error()}")
            return False

        authorized = mt5.login(self.login, password=self.password, server=self.server)
        if authorized:
            print(f"Connected to MT5 account #{self.login}")
            self.connected = True
        else:
            print(f"failed to connect at account #{self.login}, error code: {mt5.last_error()}")
        return self.connected

    def shutdown(self):
        mt5.shutdown()
        self.connected = False

    def get_symbol_info(self, symbol):
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"{symbol} not found, can not call order_check()")
            return None
        if not info.visible:
            print(f"{symbol} is not visible, trying to switch on")
            if not mt5.symbol_select(symbol, True):
                print(f"symbol_select({symbol}) failed, exit")
                return None
        return info

    def get_open_positions(self, symbol=None):
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()

        if positions is None:
            return []
            
        return positions

    def get_data(self, symbol, timeframe, num_candles=1000):
        # Convert config timeframe string (e.g., "M15") to MT5 constant if needed
        # For simplicity, assuming user maps config to MT5 constants or we do it here.
        # Mapping:
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        
        mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_M15) # Default M15

        # Ensure symbol is selected in Market Watch
        if not mt5.symbol_select(symbol, True):
            print(f"Symbol '{symbol}' not found or not visible!")
            # Try to list some available symbols to help debug
            symbols = mt5.symbols_get()
            if symbols:
                names = [s.name for s in symbols[:5]]
                print(f"Available symbols example: {names}")
            return None

        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, num_candles)
        if rates is None:
            print(f"Failed to get rates for {symbol} (Error code: {mt5.last_error()})")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def place_order(self, symbol, order_type, lots, sl=0.0, tp=0.0, deviation=20, magic=123456):
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info is None:
            return None

        action = mt5.TRADE_ACTION_DEAL
        price = 0.0
        
        if order_type == "BUY":
            mt5_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        elif order_type == "SELL":
            mt5_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            print("Invalid order type")
            return None

        request = {
            "action": action,
            "symbol": symbol,
            "volume": float(lots),
            "type": mt5_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": deviation,
            "magic": magic,
            "comment": "Antigravity Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK, 
        }

        # Check supported filling modes
        # SYMBOL_FILLING_FOK = 1
        # SYMBOL_FILLING_IOC = 2
        
        filling_mode = mt5.ORDER_FILLING_FOK
        if symbol_info.filling_mode is not None:
            # Check if FOK (bit 1) is NOT supported
            if not (symbol_info.filling_mode & 1):
                # Check if IOC (bit 2) IS supported
                if (symbol_info.filling_mode & 2):
                    filling_mode = mt5.ORDER_FILLING_IOC
                else:
                    filling_mode = mt5.ORDER_FILLING_RETURN

        request["type_filling"] = filling_mode

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed, retcode={result.retcode}")
            return None
        
        print(f"Order placed: {result}")
        return result
