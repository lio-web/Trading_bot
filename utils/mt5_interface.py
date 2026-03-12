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
        # Adding a timeout (60 seconds) so the bot doesn't freeze indefinitely if MT5 has a popup
        if not mt5.initialize(timeout=60000):
            print(f"initialize() failed or timed out, error code = {mt5.last_error()}")
            return False

        print(f"MT5 Initialized. Checking current active account...")
        
        # Give the terminal (if we just launched it) up to 10 seconds to log in automatically
        for i in range(10):
            current_account = mt5.account_info()
            if current_account is not None and str(current_account.login) == str(self.login):
                print(f"Already seamlessly connected to MT5 account #{self.login} via terminal.")
                self.connected = True
                return True
            print(f"[{i+1}/10] Waiting for terminal to settle... (Current: {current_account.login if current_account else 'None'})")
            time.sleep(1)

        # If after 10 seconds we are STILL not on the right account, explicitly attempt to login
        print(f"Attempting to force login to MT5 account #{self.login}...")
        authorized = mt5.login(int(self.login), password=self.password, server=self.server)
        if authorized:
            print(f"Successfully connected to account #{self.login}")
            self.connected = True
        else:
            print(f"Failed to connect at account #{self.login}. (Error: {mt5.last_error()})")
            print("CRITICAL: If you get IPC timeout (-10005), please open your JustMarkets MT5 application manually, log in, and leave it running!")

        return self.connected

    def shutdown(self):
        mt5.shutdown()
        self.connected = False

    def get_balance(self):
        return mt5.account_info().balance

    def get_data(self, symbol, timeframe_str, num_candles=500):
        # Map config strings to MT5 constants
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        mt5_tf = tf_map.get(timeframe_str, mt5.TIMEFRAME_H1)

        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, num_candles)
        if rates is None:
            print(f"Failed to get rates for {symbol}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def get_open_positions_count(self):
        positions = mt5.positions_get()
        if positions is None:
            return 0
        return len(positions)

    def calculate_lot_size(self, symbol, entry_price, sl_price, risk_percent):
        balance = self.get_balance()
        risk_amount = balance * risk_percent
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.01

        # Calculate distance in points
        # NOTE: This formula assumes standard forex math. 
        # For XAUUSD or crypto, verify 'trade_tick_value'.
        dist_points = abs(entry_price - sl_price) / symbol_info.point
        if dist_points == 0:
            return 0.01

        # Lot = Risk / (Points * TickValue) roughly
        # Precise: Risk / (Abs(Entry - SL) * ContractSize?)
        # Simplest consistent way:
        # Loss per lot = (Entry - SL) * TickValue / TickSize
        loss_per_lot = (abs(entry_price - sl_price) / symbol_info.trade_tick_size) * symbol_info.trade_tick_value
        
        if loss_per_lot == 0:
            return 0.01
            
        lots = risk_amount / loss_per_lot
        
        # Normalize lots
        step = symbol_info.volume_step
        lots = round(lots / step) * step
        lots = max(lots, symbol_info.volume_min)
        lots = min(lots, symbol_info.volume_max)
        
        return round(lots, 2)

    def place_order(self, symbol, order_type, lots, sl, tp):
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return None

        filling_mode = mt5.ORDER_FILLING_FOK
        # Check filling mode support (1=FOK, 2=IOC)
        if not (symbol_info.filling_mode & 1):
            if (symbol_info.filling_mode & 2):
                filling_mode = mt5.ORDER_FILLING_IOC
            else:
                filling_mode = mt5.ORDER_FILLING_RETURN

        action = mt5.TRADE_ACTION_DEAL
        mt5_type = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if order_type == "BUY" else mt5.symbol_info_tick(symbol).bid

        request = {
            "action": action,
            "symbol": symbol,
            "volume": float(lots),
            "type": mt5_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20,
            "magic": 999888,
            "comment": "SMC Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        result = mt5.order_send(request)
        return result

    def modify_position(self, ticket, sl, tp):
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": float(sl),
            "tp": float(tp)
        }
        return mt5.order_send(request)

    def close_position(self, position):
        tick = mt5.symbol_info_tick(position.symbol)
        
        # Determine the closing price and type based on the position type
        if position.type == mt5.ORDER_TYPE_BUY:
            price = tick.bid
            order_type = mt5.ORDER_TYPE_SELL
        else: # sell position
            price = tick.ask
            order_type = mt5.ORDER_TYPE_BUY

        symbol_info = mt5.symbol_info(position.symbol)
        filling_mode = mt5.ORDER_FILLING_FOK
        if not (symbol_info.filling_mode & 1):
            if (symbol_info.filling_mode & 2):
                 filling_mode = mt5.ORDER_FILLING_IOC
            else:
                 filling_mode = mt5.ORDER_FILLING_RETURN

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": position.magic,
            "comment": "Reversal Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        result = mt5.order_send(request)
        return result
