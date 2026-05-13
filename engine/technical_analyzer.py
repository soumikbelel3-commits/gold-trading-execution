"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Technical Analyzer                    ║
║   50+ indicators, multi-timeframe, Fibonacci, Ichimoku          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class GoldTechnicalAnalyzer:
    """
    Institutional-grade technical analysis engine for gold.
    Computes indicators across multiple timeframes and generates
    a scored technical outlook.
    """
    
    def __init__(self, gold_data: dict):
        """
        Args:
            gold_data: dict with keys '1h', '4h', 'daily' containing DataFrames
        """
        self.data = gold_data
        self.analysis = {}
    
    def analyze_all(self) -> dict:
        """Run full technical analysis across all timeframes."""
        result = {
            "current_price": None,
            "daily_change": None,
            "daily_change_pct": None,
            "timeframes": {},
            "key_levels": {},
            "fibonacci": {},
            "pivot_points": {},
            "ichimoku": {},
            "overall_score": 0,
            "overall_bias": "Neutral",
            "candlestick_data": {},
        }
        
        # Get current price from most recent data
        for tf in ["1h", "4h", "daily"]:
            df = self.data.get(tf, pd.DataFrame())
            if not df.empty and "Close" in df.columns:
                result["current_price"] = float(df["Close"].iloc[-1])
                if len(df) >= 2:
                    prev_close = float(df["Close"].iloc[-2])
                    result["daily_change"] = round(result["current_price"] - prev_close, 2)
                    result["daily_change_pct"] = round(
                        (result["current_price"] - prev_close) / prev_close * 100, 3
                    )
                break
        
        # Analyze each timeframe
        scores = []
        for tf_name in ["1h", "4h", "daily"]:
            df = self.data.get(tf_name, pd.DataFrame())
            if df.empty or "Close" not in df.columns:
                continue
            
            tf_result = self._analyze_timeframe(df, tf_name)
            result["timeframes"][tf_name] = tf_result
            scores.append(tf_result.get("score", 0))
        
        # Key levels from daily
        daily_df = self.data.get("daily", pd.DataFrame())
        if not daily_df.empty and "Close" in daily_df.columns:
            result["key_levels"] = self._compute_key_levels(daily_df)
            result["fibonacci"] = self._compute_fibonacci(daily_df)
            result["pivot_points"] = self._compute_pivot_points(daily_df)
            result["ichimoku"] = self._compute_ichimoku(daily_df)
            
            # Candlestick data for charting (last 120 candles)
            result["candlestick_data"]["daily"] = self._format_candles(daily_df, 120)
        
        h1_df = self.data.get("1h", pd.DataFrame())
        if not h1_df.empty:
            result["candlestick_data"]["1h"] = self._format_candles(h1_df, 200)
        
        # Overall score (weighted: daily 50%, 4h 30%, 1h 20%)
        if scores:
            weights = [0.2, 0.3, 0.5][:len(scores)]
            total_w = sum(weights)
            result["overall_score"] = round(
                sum(s * w for s, w in zip(scores, weights)) / total_w, 2
            )
        
        # Classify bias
        s = result["overall_score"]
        if s >= 3:
            result["overall_bias"] = "Strong Bullish"
        elif s >= 1.5:
            result["overall_bias"] = "Bullish"
        elif s >= 0.5:
            result["overall_bias"] = "Slightly Bullish"
        elif s > -0.5:
            result["overall_bias"] = "Neutral"
        elif s > -1.5:
            result["overall_bias"] = "Slightly Bearish"
        elif s > -3:
            result["overall_bias"] = "Bearish"
        else:
            result["overall_bias"] = "Strong Bearish"
        
        return result
    
    def _analyze_timeframe(self, df: pd.DataFrame, tf_name: str) -> dict:
        """Analyze a single timeframe."""
        close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
        high = df["High"].squeeze() if "High" in df.columns else close
        low = df["Low"].squeeze() if "Low" in df.columns else close
        volume = df["Volume"].squeeze() if "Volume" in df.columns else pd.Series(0, index=close.index)
        
        result = {"name": tf_name, "indicators": {}, "signals": {}, "score": 0}
        
        score = 0
        
        # ── Moving Averages ──
        for p in [20, 50, 100, 200]:
            if len(close) >= p:
                sma = close.rolling(p).mean()
                ema = close.ewm(span=p).mean()
                result["indicators"][f"SMA_{p}"] = round(float(sma.iloc[-1]), 2)
                result["indicators"][f"EMA_{p}"] = round(float(ema.iloc[-1]), 2)
                
                # Signal: price vs MA
                if float(close.iloc[-1]) > float(sma.iloc[-1]):
                    score += 0.5
                else:
                    score -= 0.5
        
        # Golden / Death Cross
        if len(close) >= 200:
            sma50 = close.rolling(50).mean()
            sma200 = close.rolling(200).mean()
            if float(sma50.iloc[-1]) > float(sma200.iloc[-1]):
                result["signals"]["golden_cross"] = True
                score += 1
            else:
                result["signals"]["golden_cross"] = False
                score -= 1
        
        # ── RSI (14) ──
        if len(close) >= 15:
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0).rolling(14).mean()
            loss = (-delta).where(delta < 0, 0.0).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            rsi_val = float(rsi.iloc[-1])
            result["indicators"]["RSI_14"] = round(rsi_val, 2)
            
            if rsi_val > 70:
                result["signals"]["rsi"] = "Overbought"
                score -= 1
            elif rsi_val < 30:
                result["signals"]["rsi"] = "Oversold"
                score += 1
            elif rsi_val > 55:
                result["signals"]["rsi"] = "Bullish"
                score += 0.5
            elif rsi_val < 45:
                result["signals"]["rsi"] = "Bearish"
                score -= 0.5
            else:
                result["signals"]["rsi"] = "Neutral"
        
        # ── Stochastic RSI ──
        if len(close) >= 28:
            rsi_series = rsi.dropna()
            if len(rsi_series) >= 14:
                stoch_rsi = (rsi_series - rsi_series.rolling(14).min()) / (
                    rsi_series.rolling(14).max() - rsi_series.rolling(14).min()
                ).replace(0, np.nan)
                stoch_k = stoch_rsi.rolling(3).mean() * 100
                stoch_d = stoch_k.rolling(3).mean()
                result["indicators"]["StochRSI_K"] = round(float(stoch_k.iloc[-1]), 2)
                result["indicators"]["StochRSI_D"] = round(float(stoch_d.iloc[-1]), 2)
        
        # ── MACD ──
        if len(close) >= 26:
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            result["indicators"]["MACD"] = round(float(macd_line.iloc[-1]), 4)
            result["indicators"]["MACD_Signal"] = round(float(signal_line.iloc[-1]), 4)
            result["indicators"]["MACD_Histogram"] = round(float(histogram.iloc[-1]), 4)
            
            if float(macd_line.iloc[-1]) > float(signal_line.iloc[-1]):
                result["signals"]["macd"] = "Bullish"
                score += 1
            else:
                result["signals"]["macd"] = "Bearish"
                score -= 1
            
            # Histogram momentum
            if len(histogram) >= 2:
                if float(histogram.iloc[-1]) > float(histogram.iloc[-2]):
                    result["signals"]["macd_momentum"] = "Accelerating"
                else:
                    result["signals"]["macd_momentum"] = "Decelerating"
        
        # ── Bollinger Bands ──
        if len(close) >= 20:
            bb_sma = close.rolling(20).mean()
            bb_std = close.rolling(20).std()
            bb_upper = bb_sma + 2 * bb_std
            bb_lower = bb_sma - 2 * bb_std
            bb_width = ((bb_upper - bb_lower) / bb_sma) * 100
            bb_pct = (close - bb_lower) / (bb_upper - bb_lower)
            
            result["indicators"]["BB_Upper"] = round(float(bb_upper.iloc[-1]), 2)
            result["indicators"]["BB_Middle"] = round(float(bb_sma.iloc[-1]), 2)
            result["indicators"]["BB_Lower"] = round(float(bb_lower.iloc[-1]), 2)
            result["indicators"]["BB_Width"] = round(float(bb_width.iloc[-1]), 4)
            result["indicators"]["BB_Position"] = round(float(bb_pct.iloc[-1]), 4)
            
            if float(bb_pct.iloc[-1]) > 1:
                result["signals"]["bollinger"] = "Above Upper Band"
                score -= 0.5  # mean reversion signal
            elif float(bb_pct.iloc[-1]) < 0:
                result["signals"]["bollinger"] = "Below Lower Band"
                score += 0.5
            else:
                result["signals"]["bollinger"] = "Within Bands"
        
        # ── ATR (14) ──
        if len(close) >= 15 and "High" in df.columns and "Low" in df.columns:
            tr = pd.concat([
                high - low,
                abs(high - close.shift(1)),
                abs(low - close.shift(1))
            ], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            result["indicators"]["ATR_14"] = round(float(atr.iloc[-1]), 2)
            result["indicators"]["ATR_pct"] = round(
                float(atr.iloc[-1]) / float(close.iloc[-1]) * 100, 4
            )
        
        # ── Rate of Change ──
        for p in [5, 10, 21]:
            if len(close) >= p + 1:
                roc = (close / close.shift(p) - 1) * 100
                result["indicators"][f"ROC_{p}"] = round(float(roc.iloc[-1]), 4)
        
        # ── Volume Analysis ──
        if volume.sum() > 0 and len(volume) >= 20:
            vol_sma = volume.rolling(20).mean()
            vol_ratio = volume / vol_sma
            result["indicators"]["Volume_Ratio"] = round(float(vol_ratio.iloc[-1]), 2)
            
            if float(vol_ratio.iloc[-1]) > 1.5:
                result["signals"]["volume"] = "High Volume"
            elif float(vol_ratio.iloc[-1]) < 0.5:
                result["signals"]["volume"] = "Low Volume"
            else:
                result["signals"]["volume"] = "Normal"
        
        result["score"] = round(score, 2)
        
        # Bias label
        if score >= 2:
            result["bias"] = "Bullish"
        elif score >= 0.5:
            result["bias"] = "Slightly Bullish"
        elif score > -0.5:
            result["bias"] = "Neutral"
        elif score > -2:
            result["bias"] = "Slightly Bearish"
        else:
            result["bias"] = "Bearish"
        
        return result
    
    def _compute_key_levels(self, df: pd.DataFrame) -> dict:
        """Compute support and resistance levels."""
        close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
        high = df["High"].squeeze() if isinstance(df["High"], pd.DataFrame) else df["High"]
        low = df["Low"].squeeze() if isinstance(df["Low"], pd.DataFrame) else df["Low"]
        
        levels = {}
        
        # Recent swing high/low (20-day)
        last_20 = df.tail(20)
        h20 = last_20["High"].squeeze() if isinstance(last_20["High"], pd.DataFrame) else last_20["High"]
        l20 = last_20["Low"].squeeze() if isinstance(last_20["Low"], pd.DataFrame) else last_20["Low"]
        c20 = last_20["Close"].squeeze() if isinstance(last_20["Close"], pd.DataFrame) else last_20["Close"]
        
        levels["resistance_1"] = round(float(h20.max()), 2)
        levels["support_1"] = round(float(l20.min()), 2)
        
        # 52-week high/low
        if len(df) >= 252:
            yr = df.tail(252)
            h_yr = yr["High"].squeeze() if isinstance(yr["High"], pd.DataFrame) else yr["High"]
            l_yr = yr["Low"].squeeze() if isinstance(yr["Low"], pd.DataFrame) else yr["Low"]
            levels["52w_high"] = round(float(h_yr.max()), 2)
            levels["52w_low"] = round(float(l_yr.min()), 2)
        else:
            h_all = df["High"].squeeze() if isinstance(df["High"], pd.DataFrame) else df["High"]
            l_all = df["Low"].squeeze() if isinstance(df["Low"], pd.DataFrame) else df["Low"]
            levels["52w_high"] = round(float(h_all.max()), 2)
            levels["52w_low"] = round(float(l_all.min()), 2)
        
        # Distance from highs/lows
        curr = float(close.iloc[-1])
        levels["dist_from_high_pct"] = round((levels["52w_high"] - curr) / curr * 100, 2)
        levels["dist_from_low_pct"] = round((curr - levels["52w_low"]) / levels["52w_low"] * 100, 2)
        
        return levels
    
    def _compute_fibonacci(self, df: pd.DataFrame) -> dict:
        """Compute Fibonacci retracement levels."""
        # Use 60-day swing for Fibonacci
        last_60 = df.tail(60)
        h = last_60["High"].squeeze() if isinstance(last_60["High"], pd.DataFrame) else last_60["High"]
        l = last_60["Low"].squeeze() if isinstance(last_60["Low"], pd.DataFrame) else last_60["Low"]
        
        high = float(h.max())
        low = float(l.min())
        diff = high - low
        
        fib = {
            "swing_high": round(high, 2),
            "swing_low": round(low, 2),
            "fib_0": round(high, 2),
            "fib_236": round(high - diff * 0.236, 2),
            "fib_382": round(high - diff * 0.382, 2),
            "fib_500": round(high - diff * 0.500, 2),
            "fib_618": round(high - diff * 0.618, 2),
            "fib_786": round(high - diff * 0.786, 2),
            "fib_100": round(low, 2),
        }
        
        return fib
    
    def _compute_pivot_points(self, df: pd.DataFrame) -> dict:
        """Compute Classic and Camarilla pivot points."""
        last = df.tail(1)
        h_series = last["High"].squeeze() if isinstance(last["High"], pd.DataFrame) else last["High"]
        l_series = last["Low"].squeeze() if isinstance(last["Low"], pd.DataFrame) else last["Low"]
        c_series = last["Close"].squeeze() if isinstance(last["Close"], pd.DataFrame) else last["Close"]
        
        H = float(h_series.iloc[-1]) if hasattr(h_series, 'iloc') else float(h_series)
        L = float(l_series.iloc[-1]) if hasattr(l_series, 'iloc') else float(l_series)
        C = float(c_series.iloc[-1]) if hasattr(c_series, 'iloc') else float(c_series)
        
        # Classic Pivot Points
        P = (H + L + C) / 3
        classic = {
            "PP": round(P, 2),
            "R1": round(2 * P - L, 2),
            "R2": round(P + (H - L), 2),
            "R3": round(H + 2 * (P - L), 2),
            "S1": round(2 * P - H, 2),
            "S2": round(P - (H - L), 2),
            "S3": round(L - 2 * (H - P), 2),
        }
        
        # Camarilla Pivot Points
        diff = H - L
        camarilla = {
            "R4": round(C + diff * 1.1 / 2, 2),
            "R3": round(C + diff * 1.1 / 4, 2),
            "R2": round(C + diff * 1.1 / 6, 2),
            "R1": round(C + diff * 1.1 / 12, 2),
            "S1": round(C - diff * 1.1 / 12, 2),
            "S2": round(C - diff * 1.1 / 6, 2),
            "S3": round(C - diff * 1.1 / 4, 2),
            "S4": round(C - diff * 1.1 / 2, 2),
        }
        
        return {"classic": classic, "camarilla": camarilla}
    
    def _compute_ichimoku(self, df: pd.DataFrame) -> dict:
        """Compute Ichimoku Cloud components."""
        if len(df) < 52:
            return {}
        
        close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
        high = df["High"].squeeze() if isinstance(df["High"], pd.DataFrame) else df["High"]
        low = df["Low"].squeeze() if isinstance(df["Low"], pd.DataFrame) else df["Low"]
        
        # Tenkan-sen (9-period)
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        # Kijun-sen (26-period)
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        # Senkou Span A
        span_a = ((tenkan + kijun) / 2).shift(26)
        # Senkou Span B (52-period)
        span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        
        curr_price = float(close.iloc[-1])
        
        result = {
            "tenkan_sen": round(float(tenkan.iloc[-1]), 2),
            "kijun_sen": round(float(kijun.iloc[-1]), 2),
        }
        
        # Cloud values (current future cloud)
        if not pd.isna(span_a.iloc[-1]):
            result["senkou_span_a"] = round(float(span_a.iloc[-1]), 2)
        if not pd.isna(span_b.iloc[-1]):
            result["senkou_span_b"] = round(float(span_b.iloc[-1]), 2)
        
        # Signals
        if float(tenkan.iloc[-1]) > float(kijun.iloc[-1]):
            result["tk_cross"] = "Bullish"
        else:
            result["tk_cross"] = "Bearish"
        
        if "senkou_span_a" in result and "senkou_span_b" in result:
            cloud_top = max(result["senkou_span_a"], result["senkou_span_b"])
            cloud_bottom = min(result["senkou_span_a"], result["senkou_span_b"])
            if curr_price > cloud_top:
                result["cloud_position"] = "Above Cloud (Bullish)"
            elif curr_price < cloud_bottom:
                result["cloud_position"] = "Below Cloud (Bearish)"
            else:
                result["cloud_position"] = "Inside Cloud (Neutral)"
        
        return result
    
    def _format_candles(self, df: pd.DataFrame, n: int) -> list:
        """Format candlestick data for frontend charting."""
        recent = df.tail(n)
        candles = []
        
        for idx, row in recent.iterrows():
            try:
                ts = idx
                if hasattr(ts, 'timestamp'):
                    time_val = int(ts.timestamp())
                else:
                    time_val = int(pd.Timestamp(ts).timestamp())
                
                o = float(row["Open"]) if not pd.isna(row.get("Open", np.nan)) else float(row["Close"])
                h = float(row["High"]) if not pd.isna(row.get("High", np.nan)) else float(row["Close"])
                l = float(row["Low"]) if not pd.isna(row.get("Low", np.nan)) else float(row["Close"])
                c = float(row["Close"])
                
                candles.append({
                    "time": time_val,
                    "open": round(o, 2),
                    "high": round(h, 2),
                    "low": round(l, 2),
                    "close": round(c, 2),
                })
            except:
                continue
        
        return candles
