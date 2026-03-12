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
    def identify_fvgs(df):
        """
        Identifies Fair Value Gaps (FVG) using the last 3 candles.
        Bullish FVG: Low of candle 3 > High of candle 1
        Bearish FVG: High of candle 3 < Low of candle 1
        """
        if len(df) < 3:
            return None
        
        c1 = df.iloc[-3]
        c3 = df.iloc[-1]

        if c3['low'] > c1['high']:
            return {"type": "Bullish", "bottom": c1['high'], "top": c3['low']}
        elif c3['high'] < c1['low']:
            return {"type": "Bearish", "top": c1['low'], "bottom": c3['high']}
        
        return None

    @staticmethod
    def identify_order_blocks(df, lookback=20):
        """
        Simple Order Block (OB) identification within a recent lookback window.
        """
        if len(df) < lookback:
            return None
        
        recent_df = df.iloc[-lookback:]
        
        # Bullish OB (Red candle at local bottom)
        low_idx = recent_df['low'].idxmin()
        ob_b_candle = recent_df.loc[low_idx]
        
        if ob_b_candle['close'] < ob_b_candle['open']:
            return {"type": "Bullish", "top": ob_b_candle['high'], "bottom": ob_b_candle['low']}
                
        # Bearish OB (Green candle at local top)
        high_idx = recent_df['high'].idxmax()
        ob_br_candle = recent_df.loc[high_idx]
        if ob_br_candle['close'] > ob_br_candle['open']:
            return {"type": "Bearish", "top": ob_br_candle['high'], "bottom": ob_br_candle['low']}
                
        return None

    @staticmethod
    def identify_liquidity(df, window=5):
        """
        Identifies significant swing highs and lows as liquidity pools.
        """
        if len(df) < window * 2 + 1:
            return None
            
        recent_df = df.iloc[-(window*2 + 1):]
        middle_idx = recent_df.index[window]
        middle_candle = recent_df.loc[middle_idx]
        
        is_swing_high = True
        is_swing_low = True
        
        for i in recent_df.index:
            if i == middle_idx:
                continue
            if recent_df['high'].loc[i] >= middle_candle['high']:
                is_swing_high = False
            if recent_df['low'].loc[i] <= middle_candle['low']:
                is_swing_low = False
                
        if is_swing_high:
            return {"type": "BuySide", "level": middle_candle['high']}
        elif is_swing_low:
            return {"type": "SellSide", "level": middle_candle['low']}
            
        return None

    @staticmethod
    def identify_trend(df, lookback=50):
        """
        Basic trend identification using moving highs and lows.
        """
        if len(df) < lookback:
            return "Neutral"
        
        start_price = df.iloc[-lookback]['close']
        end_price = df.iloc[-1]['close']
        
        if end_price > start_price * 1.005:
            return "Uptrend"
        elif end_price < start_price * 0.995:
            return "Downtrend"
            
        return "Neutral"

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
            
        # Identify SMC Concepts
        fvg = TechnicalAnalysis.identify_fvgs(df)
        ob = TechnicalAnalysis.identify_order_blocks(df)
        trend = TechnicalAnalysis.identify_trend(df)
        
        # Basic Strategy combining traditional and SMC
        if pattern and not signal:
            if pattern in ["Bullish Engulfing", "Hammer"] and (close < bbl or rsi < 40 or trend == "Uptrend"):
                signal = "BUY"
            elif pattern in ["Bearish Engulfing", "Shooting Star"] and (close > bbu or rsi > 60 or trend == "Downtrend"):
                signal = "SELL"
                
        # SMC Confluence: Tap into FVG or OB
        if fvg:
            if fvg['type'] == 'Bullish' and fvg['bottom'] <= close <= fvg['top'] and trend != "Downtrend":
                signal = "BUY"
                pattern = "Bullish FVG Tap"
            elif fvg['type'] == 'Bearish' and fvg['bottom'] <= close <= fvg['top'] and trend != "Uptrend":
                signal = "SELL"
                pattern = "Bearish FVG Tap"
                
        if ob and not signal:
            if ob['type'] == 'Bullish' and ob['bottom'] <= close <= ob['top'] and trend != "Downtrend":
                signal = "BUY"
                pattern = "Bullish OB Tap"
            elif ob['type'] == 'Bearish' and ob['bottom'] <= close <= ob['top'] and trend != "Uptrend":
                signal = "SELL"
                pattern = "Bearish OB Tap"
                
        # Classic Strong Signal (RSI + Stoch)
        if not signal:
            if close < bbl and rsi < 30 and stoch_k < 20:
                signal = "BUY"
                pattern = "Classic Oversold"
            elif close > bbu and rsi > 70 and stoch_k > 80:
                signal = "SELL"
                pattern = "Classic Overbought"

        return signal, pattern
