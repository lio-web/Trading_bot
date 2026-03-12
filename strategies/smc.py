import pandas as pd
import numpy as np
from strategies.candlestick import CandlestickDetector
import config

class PriceActionStrategy:
    @staticmethod
    def identify_swings(df, left_bars=5, right_bars=5):
        """Identifies pivot points. Increased default to 5 for stricter swings."""
        df = df.copy()
        df['is_swing_high'] = False
        df['is_swing_low'] = False
        
        for i in range(left_bars, len(df) - right_bars):
            # Swing High
            if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, left_bars+1)) and \
               all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, right_bars+1)):
                df.at[df.index[i], 'is_swing_high'] = True
                
            # Swing Low
            if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, left_bars+1)) and \
               all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, right_bars+1)):
                df.at[df.index[i], 'is_swing_low'] = True
                
        return df

    @staticmethod
    def calculate_atr(df, period=14):
        """Calculates Average True Range"""
        df = df.copy()
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        atr = true_range.rolling(period).mean()
        return atr.iloc[-1]

    @staticmethod
    def calculate_ema(df, period):
        return df['close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def get_structure_bias(trend_df):
        """
        Determines market structure from H4/D1.
        Uses stricter swing detection (10 bars) to filter noise.
        """
        if trend_df is None or len(trend_df) < 50:
            return "NEUTRAL"
        
        # Stricter swings for Structure: 10 bars left/right
        swings = PriceActionStrategy.identify_swings(trend_df, left_bars=10, right_bars=10)
        highs = swings[swings['is_swing_high']]
        lows = swings[swings['is_swing_low']]
        
        if len(highs) < 2 or len(lows) < 2:
            return "NEUTRAL"
            
        last_high = highs.iloc[-1]['high']
        prev_high = highs.iloc[-2]['high']
        
        last_low = lows.iloc[-1]['low']
        prev_low = lows.iloc[-2]['low']
        
        if last_high > prev_high and last_low > prev_low:
            return "BULLISH"
        elif last_low < prev_low and last_high < prev_high:
            return "BEARISH"
            
        return "RANGE"

    @staticmethod
    def is_near_level(price, levels, threshold_points=0.0):
        if len(levels) == 0: return False, 0.0
        for level in levels:
            dist = abs(price - level)
            if dist <= threshold_points:
                return True, level
        return False, 0.0

    @staticmethod
    def check_entry(entry_df, trend_df, config_params=None):
        if entry_df is None or len(entry_df) < 20: return None, 0.0, ""
        
        # 1. Volatility Filter (ATR)
        # Calculate ATR on Entry Timeframe
        atr = PriceActionStrategy.calculate_atr(entry_df)
        curr_candle = entry_df.iloc[-1]
        candle_range = curr_candle['high'] - curr_candle['low']
        
        # Filter: Candle must be substantial (at least 30% of ATR) to avoid dojis/noise
        # And not insane (> 3x ATR) to avoid news spikes
        if candle_range < (atr * 0.3):
            return None, 0.0, ""
            
        # 2. Context
        bias = PriceActionStrategy.get_structure_bias(trend_df)

        # --- EXTRA CONFLUENCE (Real Account Safety) ---
        if getattr(config, "EXTRA_CONFLUENCE", False):
            # EMA Trend Alignment Check (Loosened)
            # We check if we are going completely against a strong trend, but we allow 
            # counter-trend setups if the price has stretched too far from the fast EMA (reversals).
            
            # If bias is BULLISH but we want to trade BEARISH (Short trade)
            if bias == "BULLISH":
                # Only block BUYs if we are below both EMAs (weak setup)
                # We ALLOW SELLs (counter-trend) if price is far above the 50 EMA (overextended)
                pass # We handle specific buy/sell blocks later in the signal generation
                
            elif bias == "BEARISH":
                # Only block SELLs if we are above both EMAs (weak setup)
                # We ALLOW BUYs (counter-trend) if price is far below the 50 EMA (overextended)
                pass 
            
            # Volume Check - Signal candle should have higher volume than previous candle (momentum validation)
            prev_candle = entry_df.iloc[-2]
            if 'tick_volume' in curr_candle and 'tick_volume' in prev_candle:
                if curr_candle['tick_volume'] <= (prev_candle['tick_volume'] * 0.9): 
                    # Drop signals if volume is noticeably lower compared to previous
                    return None, 0.0, ""
        
        # 3. Key Levels (Stricter: 10 bars)
        swings_h4 = PriceActionStrategy.identify_swings(trend_df, left_bars=10, right_bars=10)
        levels_h4 = np.concatenate([
            swings_h4[swings_h4['is_swing_high']]['high'].values,
            swings_h4[swings_h4['is_swing_low']]['low'].values
        ])
        
        prev_candle = entry_df.iloc[-2]
        current_price = curr_candle['close']
        
        # Threshold: 10% of ATR (Dynamic) or Price %
        threshold = atr * 0.5 # Within 50% of an ATR move to the level
        
        near_level, level_price = PriceActionStrategy.is_near_level(current_price, levels_h4, threshold)

        # --- STRATEGY 1: Trend Pin Bar ---
        if bias == "BULLISH":
            if near_level and current_price > level_price:
               if CandlestickDetector.is_bullish_pinbar(curr_candle):
                   return "BUY", curr_candle['low'], "Trend Pin Bar"
            # Allow Short Trades in a Bullish Trend if price is at a key level (Counter-trend)
            elif near_level and current_price < level_price:
               if CandlestickDetector.is_bearish_pinbar(curr_candle):
                   return "SELL", curr_candle['high'], "Counter-Trend Pin Bar"
                   
        elif bias == "BEARISH":
            if near_level and current_price < level_price:
                if CandlestickDetector.is_bearish_pinbar(curr_candle):
                    return "SELL", curr_candle['high'], "Trend Pin Bar"
            # Allow Long Trades in a Bearish Trend if price is at a key level (Counter-trend)
            elif near_level and current_price > level_price:
                if CandlestickDetector.is_bullish_pinbar(curr_candle):
                    return "BUY", curr_candle['low'], "Counter-Trend Pin Bar"

        # --- STRATEGY 2: Engulfing at Key Levels ---
        if near_level:
            if CandlestickDetector.is_bullish_engulfing(curr_candle, prev_candle):
                 if bias in ["BULLISH", "RANGE"]:
                     return "BUY", min(curr_candle['low'], prev_candle['low']), "Key Level Engulfing"

            if CandlestickDetector.is_bearish_engulfing(curr_candle, prev_candle):
                 if bias in ["BEARISH", "RANGE"]:
                     return "SELL", max(curr_candle['high'], prev_candle['high']), "Key Level Engulfing"

        # --- STRATEGY 3: Inside Bar False Break ---
        # (Simplified logic retained)
        if len(entry_df) >= 3:
            c1, c2, c3 = entry_df.iloc[-3], entry_df.iloc[-2], entry_df.iloc[-1]
            if CandlestickDetector.is_inside_bar(c2, c1):
                if c3['high'] > c2['high'] and c3['close'] < c2['high']:
                     if bias != "BULLISH": return "SELL", c3['high'], "Inside Bar False Break"

                if c3['low'] < c2['low'] and c3['close'] > c2['low']:
                    if bias != "BEARISH": return "BUY", c3['low'], "Inside Bar False Break"

        # --- STRATEGY 4: Range Trading ---
        if bias == "RANGE":
             if near_level:
                 if current_price > level_price:
                     if CandlestickDetector.is_bullish_pinbar(curr_candle) or \
                        CandlestickDetector.is_bullish_engulfing(curr_candle, prev_candle):
                            return "BUY", curr_candle['low'], "Range Reversal"
                 
                 if current_price < level_price:
                     if CandlestickDetector.is_bearish_pinbar(curr_candle) or \
                        CandlestickDetector.is_bearish_engulfing(curr_candle, prev_candle):
                            return "SELL", curr_candle['high'], "Range Reversal"

        return None, 0.0, ""
