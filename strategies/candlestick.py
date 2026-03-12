import pandas as pd
import numpy as np

class CandlestickDetector:
    @staticmethod
    def get_candle_props(row):
        """Helper to get candle properties"""
        close = row['close']
        open_ = row['open']
        high = row['high']
        low = row['low']
        
        body_size = abs(close - open_)
        upper_wick = high - max(close, open_)
        lower_wick = min(close, open_) - low
        total_range = high - low
        
        # Avoid division by zero
        if total_range == 0:
            return 0, 0, 0, 0, False
            
        color = "GREEN" if close > open_ else "RED"
        
        return body_size, upper_wick, lower_wick, total_range, color

    @staticmethod
    def is_bullish_pinbar(row):
        """
        Bullish Pin Bar (Hammer):
        - Lower wick >= 2x body
        - Close in top 30% of candle
        """
        body, upper, lower, rng, color = CandlestickDetector.get_candle_props(row)
        if rng == 0: return False
        
        # 1. Lower wick >= 2x body
        # Handle small body case (avoid comparing to 0 weirdly, but 2*0 is 0 so it works)
        # If body is tiny (doji), it's still good if wick is long.
        is_long_wick = lower >= (2 * body)
        
        # 2. Close in top 30%
        # Location of close relative to low: (Close - Low) / Range
        close_loc = (row['close'] - row['low']) / rng
        is_top_30 = close_loc >= 0.70
        
        return is_long_wick and is_top_30

    @staticmethod
    def is_bearish_pinbar(row):
        """
        Bearish Pin Bar (Shooting Star):
        - Upper wick >= 2x body
        - Close in bottom 30%
        """
        body, upper, lower, rng, color = CandlestickDetector.get_candle_props(row)
        if rng == 0: return False
        
        # 1. Upper wick >= 2x body
        is_long_wick = upper >= (2 * body)
        
        # 2. Close in bottom 30%
        # Location of close relative to low
        close_loc = (row['close'] - row['low']) / rng
        is_bottom_30 = close_loc <= 0.30
        
        return is_long_wick and is_bottom_30

    @staticmethod
    def is_bullish_engulfing(curr, prev):
        """
        Bullish Engulfing:
        - Previous candle Red
        - Current candle Green
        - Current Open <= Previous Close (gap down or equal) - strict definition varies, 
          but generally Body engulfs Body.
        - Current Close > Previous Open
        """
        # Prev Red
        if prev['close'] >= prev['open']: return False
        # Curr Green
        if curr['close'] <= curr['open']: return False
        
        # Body Engulfs Body
        prev_top = prev['open']
        prev_bottom = prev['close']
        
        curr_top = curr['close']
        curr_bottom = curr['open']
        
        return (curr_top > prev_top) and (curr_bottom < prev_bottom)

    @staticmethod
    def is_bearish_engulfing(curr, prev):
        """
        Bearish Engulfing:
        - Previous candle Green
        - Current candle Red
        - Body engulfs Body
        """
        # Prev Green
        if prev['close'] <= prev['open']: return False
        # Curr Red
        if curr['close'] >= curr['open']: return False
        
        prev_top = prev['close']
        prev_bottom = prev['open']
        
        curr_top = curr['open']
        curr_bottom = curr['close']
        
        return (curr_top > prev_top) and (curr_bottom < prev_bottom)

    @staticmethod
    def is_inside_bar(curr, prev):
        """
        Inside Bar:
        - Current High <= Previous High
        - Current Low >= Previous Low
        """
        return (curr['high'] < prev['high']) and (curr['low'] > prev['low'])
