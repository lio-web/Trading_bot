import pandas_ta as ta
import pandas as pd

class TechnicalAnalysis:
    @staticmethod
    def calculate_indicators(df):
        """
        Calculates RSI, Bollinger Bands, SMA, Stochastic, and generates DataFrame with these columns.
        """
        if df is None or df.empty:
            return df

        # RSI
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20, std=2.0)
        # bbands returns lower, mid, upper columns. We need to rename or identify them.
        # Usually: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
        df = pd.concat([df, bb], axis=1)

        # SMA
        df['SMA'] = ta.sma(df['close'], length=50)

        # Stochastic
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
        df = pd.concat([df, stoch], axis=1)

        # Fibonacci Levels (Auto-calculated based on lookback period high/low)
        # Using a simple lookback of 100 candles for High and Low
        lookback = 100
        df['RollingHigh'] = df['high'].rolling(lookback).max()
        df['RollingLow'] = df['low'].rolling(lookback).min()
        
        df['Fib_0'] = df['RollingLow']
        df['Fib_100'] = df['RollingHigh']
        diff = df['Fib_100'] - df['Fib_0']
        
        df['Fib_23.6'] = df['Fib_0'] + diff * 0.236
        df['Fib_38.2'] = df['Fib_0'] + diff * 0.382
        df['Fib_50.0'] = df['Fib_0'] + diff * 0.500
        df['Fib_61.8'] = df['Fib_0'] + diff * 0.618
        
        return df

    @staticmethod
    def is_bullish_engulfing(current, previous):
        # Green candle completely engulfs previous Red candle
        # Current Green: Close > Open
        # Previous Red: Close < Open
        # Current Open < Previous Close AND Current Close > Previous Open
        if (current['close'] > current['open']) and (previous['close'] < previous['open']):
            if (current['open'] <= previous['close']) and (current['close'] >= previous['open']):
                return True
        return False

    @staticmethod
    def is_bearish_engulfing(current, previous):
        # Red candle completely engulfs previous Green candle
        if (current['close'] < current['open']) and (previous['close'] > previous['open']):
            if (current['open'] >= previous['close']) and (current['close'] <= previous['open']):
                return True
        return False

    @staticmethod
    def is_hammer(candle):
        # Small body at top, long lower wick (at least 2x body)
        body = abs(candle['close'] - candle['open'])
        lower_wick = min(candle['close'], candle['open']) - candle['low']
        upper_wick = candle['high'] - max(candle['close'], candle['open'])
        
        # Avoid zero division
        if body == 0:
            return False
            
        return (lower_wick >= 2 * body) and (upper_wick <= body * 0.5)

    @staticmethod
    def is_shooting_star(candle):
        # Small body at bottom, long upper wick (at least 2x body)
        body = abs(candle['close'] - candle['open'])
        upper_wick = candle['high'] - max(candle['close'], candle['open'])
        lower_wick = min(candle['close'], candle['open']) - candle['low']
        
        if body == 0:
            return False
            
        return (upper_wick >= 2 * body) and (lower_wick <= body * 0.5)

    @staticmethod
    def check_signals(df):
        """
        Analyzes the latest candle to generate buy/sell signals.
        Returns: ('BUY'|'SELL'|None, Pattern_Name|None)
        """
        if df is None or len(df) < 2:
            return None, None
            
        # Get latest closed candle and previous candle
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Dynamic lookup for BB columns
        try:
            bbl_col = [c for c in df.columns if c.startswith('BBL')][0]
            bbu_col = [c for c in df.columns if c.startswith('BBU')][0]
            stoch_k_col = [c for c in df.columns if c.startswith('STOCHk')][0]
        except IndexError:
            return None, None
        
        close = latest['close']
        rsi = latest['RSI']
        bbl = latest[bbl_col]
        bbu = latest[bbu_col]
        stoch_k = latest[stoch_k_col]
        
        signal = None
        pattern = None
        
        # Check Patterns
        if TechnicalAnalysis.is_bullish_engulfing(latest, prev):
            pattern = "Bullish Engulfing"
        elif TechnicalAnalysis.is_hammer(latest):
            pattern = "Hammer"
        elif TechnicalAnalysis.is_bearish_engulfing(latest, prev):
            pattern = "Bearish Engulfing"
        elif TechnicalAnalysis.is_shooting_star(latest):
            pattern = "Shooting Star"
            
        # BUY Logic (Confluence)
        # 1. Price near lower band
        # 2. RSI oversold OR (RSI low-ish AND Bullish Pattern)
        if close < bbl or (close < bbl * 1.001): # Near Lower Band
            if (rsi < 30 and stoch_k < 20): # Classic Strong Signal
                signal = "BUY"
            elif (rsi < 45 and pattern in ["Bullish Engulfing", "Hammer"]): # Pattern Confirmation
                signal = "BUY"
            
        # SELL Logic (Confluence)
        elif close > bbu or (close > bbu * 0.999): # Near Upper Band
            if (rsi > 70 and stoch_k > 80): # Classic Strong Signal
                signal = "SELL"
            elif (rsi > 55 and pattern in ["Bearish Engulfing", "Shooting Star"]): # Pattern Confirmation
                signal = "SELL"
            
        return signal, pattern
