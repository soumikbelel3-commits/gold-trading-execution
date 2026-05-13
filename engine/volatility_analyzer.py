"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Volatility Analyzer                   ║
║   Vol surface, regime detection, percentile ranking              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np


class GoldVolatilityAnalyzer:
    """
    Analyzes gold volatility regime for session preparation.
    """
    
    def __init__(self, gold_data: dict, vix: float = None):
        self.data = gold_data
        self.vix = vix
    
    def analyze(self) -> dict:
        """Full volatility analysis."""
        result = {
            "historical_vol": {},
            "vol_percentile": None,
            "term_structure": "Unknown",
            "expected_range": {},
            "regime": "Normal",
            "vol_score": 0,
        }
        
        daily = self.data.get("daily", pd.DataFrame())
        if daily.empty or "Close" not in daily.columns:
            return result
        
        close = daily["Close"].squeeze() if isinstance(daily["Close"], pd.DataFrame) else daily["Close"]
        high = daily["High"].squeeze() if "High" in daily.columns else close
        low = daily["Low"].squeeze() if "Low" in daily.columns else close
        
        returns = np.log(close / close.shift(1)).dropna()
        
        # ── Historical Volatility at Multiple Windows ──
        windows = {"5d": 5, "10d": 10, "20d": 20, "60d": 60, "120d": 120}
        for name, w in windows.items():
            if len(returns) >= w:
                hv = float(returns.rolling(w).std().iloc[-1]) * np.sqrt(252) * 100
                result["historical_vol"][name] = round(hv, 2)
        
        # ── Volatility Percentile (where is current vol vs 1yr history) ──
        if len(returns) >= 252:
            rolling_20d_vol = returns.rolling(20).std() * np.sqrt(252) * 100
            rolling_20d_vol = rolling_20d_vol.dropna()
            current_vol = rolling_20d_vol.iloc[-1]
            percentile = float((rolling_20d_vol <= current_vol).mean() * 100)
            result["vol_percentile"] = round(percentile, 1)
        elif "20d" in result["historical_vol"]:
            result["vol_percentile"] = 50.0  # default
        
        # ── Vol Term Structure (near-term vs long-term) ──
        hv = result["historical_vol"]
        if "5d" in hv and "60d" in hv:
            if hv["5d"] > hv["60d"] * 1.2:
                result["term_structure"] = "Backwardation (Near > Long)"
                result["vol_score"] += 1  # vol event in progress
            elif hv["5d"] < hv["60d"] * 0.8:
                result["term_structure"] = "Contango (Long > Near)"
                result["vol_score"] -= 0.5
            else:
                result["term_structure"] = "Flat"
        
        # ── Expected Daily Range (ATR-based) ──
        if "High" in daily.columns and "Low" in daily.columns and len(daily) >= 15:
            tr = pd.concat([
                high - low,
                abs(high - close.shift(1)),
                abs(low - close.shift(1))
            ], axis=1).max(axis=1)
            
            atr_14 = float(tr.rolling(14).mean().iloc[-1])
            current_price = float(close.iloc[-1])
            
            result["expected_range"] = {
                "atr_14": round(atr_14, 2),
                "atr_pct": round(atr_14 / current_price * 100, 4),
                "expected_high": round(current_price + atr_14, 2),
                "expected_low": round(current_price - atr_14, 2),
                "range_1_5x": round(atr_14 * 1.5, 2),
                "range_2x": round(atr_14 * 2, 2),
            }
        
        # ── Parkinson Volatility (range-based, more efficient) ──
        if "High" in daily.columns and "Low" in daily.columns and len(daily) >= 21:
            parkinson = np.sqrt(
                (1 / (4 * np.log(2))) *
                (np.log(high / low) ** 2).rolling(21).mean()
            ) * np.sqrt(252) * 100
            result["historical_vol"]["parkinson_21d"] = round(float(parkinson.iloc[-1]), 2)
        
        # ── Volatility Regime Classification ──
        vol_20d = result["historical_vol"].get("20d", 15)
        if vol_20d > 30:
            result["regime"] = "Extreme Volatility"
            result["vol_score"] += 2
        elif vol_20d > 22:
            result["regime"] = "High Volatility"
            result["vol_score"] += 1
        elif vol_20d > 14:
            result["regime"] = "Normal Volatility"
        elif vol_20d > 8:
            result["regime"] = "Low Volatility"
            result["vol_score"] -= 1
        else:
            result["regime"] = "Extremely Low Volatility"
            result["vol_score"] -= 1
        
        # ── VIX Context ──
        if self.vix is not None:
            result["vix"] = {
                "value": self.vix,
                "gold_implication": self._vix_gold_implication(self.vix)
            }
        
        result["vol_score"] = round(result["vol_score"], 2)
        
        return result
    
    def _vix_gold_implication(self, vix: float) -> str:
        if vix > 30:
            return "Extreme fear — gold likely in demand as safe haven"
        elif vix > 22:
            return "Elevated fear — supportive for gold"
        elif vix > 16:
            return "Normal — neutral for gold"
        elif vix > 12:
            return "Complacency — risk-on, less gold demand"
        else:
            return "Extreme complacency — low gold safe-haven demand"
