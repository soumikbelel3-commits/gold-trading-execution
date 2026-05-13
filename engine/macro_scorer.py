"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Macro Scorer                          ║
║   DXY, real yields, VIX, treasury curve, oil correlation         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import numpy as np


class GoldMacroScorer:
    """
    Institutional macro environment scorer for gold trading.
    
    Scores each factor on -3 to +3 scale:
      +3 = Strongly bullish for gold
      -3 = Strongly bearish for gold
    
    Factors and their gold relationship:
      DXY ↓ → Gold ↑ (inverse)
      Real Yields ↓ → Gold ↑ (inverse, gold = zero-yield asset)
      VIX ↑ → Gold ↑ (safe haven demand)
      Yield Curve Inversion → Gold ↑ (recession fear)
      Oil ↑ → Gold ↑ (inflation hedge)
      Central Bank Hawkish → Gold ↓
    """
    
    def __init__(self, dxy: float = None, vix: float = None, 
                 yields: dict = None, cross_assets: dict = None):
        self.dxy = dxy
        self.vix = vix
        self.yields = yields or {}
        self.cross_assets = cross_assets or {}
    
    def score_all(self) -> dict:
        """Run all macro scores and produce composite."""
        result = {
            "factors": {},
            "composite_score": 0,
            "max_possible": 18,  # 6 factors × 3
            "regime": "Neutral",
            "details": {},
        }
        
        # 1. DXY Score
        dxy_score, dxy_detail = self._score_dxy()
        result["factors"]["DXY"] = {"score": dxy_score, "detail": dxy_detail, "value": self.dxy}
        
        # 2. VIX Score (Fear/Safe Haven)
        vix_score, vix_detail = self._score_vix()
        result["factors"]["VIX"] = {"score": vix_score, "detail": vix_detail, "value": self.vix}
        
        # 3. Treasury Yields Score
        yield_score, yield_detail = self._score_yields()
        result["factors"]["Yields"] = {"score": yield_score, "detail": yield_detail, 
                                        "value": self.yields.get("US10Y")}
        
        # 4. Yield Curve Score
        curve_score, curve_detail = self._score_yield_curve()
        result["factors"]["Yield_Curve"] = {"score": curve_score, "detail": curve_detail,
                                             "value": self.yields.get("curve_spread")}
        
        # 5. Oil Impact Score
        oil_score, oil_detail = self._score_oil()
        result["factors"]["Oil"] = {"score": oil_score, "detail": oil_detail}
        
        # 6. Central Bank Stance (structural)
        cb_score, cb_detail = self._score_central_bank()
        result["factors"]["Central_Bank"] = {"score": cb_score, "detail": cb_detail}
        
        # Composite
        total = sum(f["score"] for f in result["factors"].values())
        result["composite_score"] = round(total, 2)
        
        # Normalize to -1 to +1
        result["normalized_score"] = round(total / result["max_possible"], 4)
        
        # Regime classification
        if total >= 8:
            result["regime"] = "Strongly Bullish Gold"
        elif total >= 4:
            result["regime"] = "Bullish Gold"
        elif total >= 1:
            result["regime"] = "Mildly Bullish Gold"
        elif total > -1:
            result["regime"] = "Neutral"
        elif total > -4:
            result["regime"] = "Mildly Bearish Gold"
        elif total > -8:
            result["regime"] = "Bearish Gold"
        else:
            result["regime"] = "Strongly Bearish Gold"
        
        return result
    
    def _score_dxy(self) -> tuple:
        """
        DXY → Gold inverse correlation.
        DXY < 100: Strong gold tailwind
        DXY 100-103: Neutral to slightly supportive
        DXY 103-106: Headwind
        DXY > 106: Strong headwind
        """
        if self.dxy is None:
            return 0, "No DXY data"
        
        if self.dxy < 98:
            return 3, f"DXY at {self.dxy:.1f} — extremely weak dollar, strong gold tailwind"
        elif self.dxy < 100:
            return 2, f"DXY at {self.dxy:.1f} — weak dollar, bullish for gold"
        elif self.dxy < 103:
            return 1, f"DXY at {self.dxy:.1f} — mild dollar weakness, slightly supportive"
        elif self.dxy < 105:
            return 0, f"DXY at {self.dxy:.1f} — neutral territory"
        elif self.dxy < 107:
            return -1, f"DXY at {self.dxy:.1f} — strong dollar, mild headwind"
        elif self.dxy < 110:
            return -2, f"DXY at {self.dxy:.1f} — very strong dollar, gold under pressure"
        else:
            return -3, f"DXY at {self.dxy:.1f} — extremely strong dollar, significant headwind"
    
    def _score_vix(self) -> tuple:
        """
        VIX → Gold safe-haven demand.
        VIX > 30: Extreme fear → gold demand surge
        VIX 20-30: Elevated → gold support
        VIX 15-20: Normal → neutral
        VIX < 15: Complacency → less demand for haven
        """
        if self.vix is None:
            return 0, "No VIX data"
        
        if self.vix > 35:
            return 3, f"VIX at {self.vix:.1f} — extreme fear, strong safe-haven bid for gold"
        elif self.vix > 28:
            return 2, f"VIX at {self.vix:.1f} — high fear, significant gold demand"
        elif self.vix > 22:
            return 1, f"VIX at {self.vix:.1f} — elevated fear, mild gold support"
        elif self.vix > 16:
            return 0, f"VIX at {self.vix:.1f} — normal volatility, neutral for gold"
        elif self.vix > 12:
            return -1, f"VIX at {self.vix:.1f} — low fear, risk-on reduces gold appeal"
        else:
            return -2, f"VIX at {self.vix:.1f} — extreme complacency, gold demand weak"
    
    def _score_yields(self) -> tuple:
        """
        Real/Nominal Yields → Gold opportunity cost.
        Higher real yields = bearish for gold (opportunity cost)
        Lower/negative real yields = bullish for gold
        """
        us10y = self.yields.get("US10Y")
        if us10y is None:
            return 0, "No yield data"
        
        # Using 10Y nominal as proxy (in absence of TIPS data)
        if us10y < 3.0:
            return 2, f"10Y at {us10y:.2f}% — low yields supportive for gold"
        elif us10y < 3.8:
            return 1, f"10Y at {us10y:.2f}% — moderate yields, mildly supportive"
        elif us10y < 4.5:
            return 0, f"10Y at {us10y:.2f}% — neutral territory"
        elif us10y < 5.0:
            return -1, f"10Y at {us10y:.2f}% — elevated yields, mild gold headwind"
        else:
            return -2, f"10Y at {us10y:.2f}% — high yields, significant opportunity cost"
    
    def _score_yield_curve(self) -> tuple:
        """
        Yield curve (10Y-2Y spread).
        Inverted curve → recession fear → gold bullish
        Normal curve → growth → neutral to bearish gold
        """
        spread = self.yields.get("curve_spread")
        if spread is None:
            return 0, "No yield curve data"
        
        if spread < -0.5:
            return 2, f"Yield curve deeply inverted ({spread:.2f}%) — recession risk, bullish gold"
        elif spread < 0:
            return 1, f"Yield curve inverted ({spread:.2f}%) — caution, gold support"
        elif spread < 0.5:
            return 0, f"Yield curve flat ({spread:.2f}%) — neutral"
        elif spread < 1.5:
            return -1, f"Yield curve normal ({spread:.2f}%) — growth expectation, less gold demand"
        else:
            return -1, f"Yield curve steep ({spread:.2f}%) — strong growth expectations"
    
    def _score_oil(self) -> tuple:
        """
        Oil → Gold correlation through inflation channel.
        Rising oil → inflation hedge demand → gold support
        """
        oil_data = self.cross_assets.get("CrudeOil")
        if oil_data is None or (hasattr(oil_data, 'empty') and oil_data.empty):
            return 0, "No oil data"
        
        try:
            close = oil_data["Close"].squeeze() if isinstance(oil_data["Close"], __import__('pandas').DataFrame) else oil_data["Close"]
            if len(close) >= 20:
                current = float(close.iloc[-1])
                sma20 = float(close.rolling(20).mean().iloc[-1])
                pct_change = ((current - sma20) / sma20) * 100
                
                if pct_change > 10:
                    return 2, f"Oil surging +{pct_change:.1f}% above 20-SMA — inflation hedge bid for gold"
                elif pct_change > 3:
                    return 1, f"Oil rising +{pct_change:.1f}% above 20-SMA — mild inflation support"
                elif pct_change > -3:
                    return 0, f"Oil stable at {pct_change:+.1f}% vs 20-SMA — neutral"
                elif pct_change > -10:
                    return -1, f"Oil falling {pct_change:.1f}% below 20-SMA — deflationary pressure"
                else:
                    return -2, f"Oil collapsing {pct_change:.1f}% below 20-SMA — deflation fear"
        except:
            pass
        
        return 0, "Oil data insufficient"
    
    def _score_central_bank(self) -> tuple:
        """
        Central bank stance — structural factor.
        Based on yield level trends as proxy for rate expectations.
        """
        us10y = self.yields.get("US10Y")
        if us10y is None:
            return 1, "Central bank buying remains structural support (default assumption)"
        
        # If yields are dropping → dovish pivot expected → gold bullish
        # If yields are rising → hawkish → gold pressure
        # We use current level as proxy
        if us10y < 3.5:
            return 2, "Dovish rate environment — strongly supportive for gold"
        elif us10y < 4.2:
            return 1, "Moderately dovish — central bank support for gold"
        elif us10y < 4.8:
            return 0, "Neutral rate environment"
        else:
            return -1, "Hawkish rate environment — headwind for gold"
