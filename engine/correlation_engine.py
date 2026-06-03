"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Correlation Engine                    ║
║   Cross-asset correlation matrix and regime detection            ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np


class GoldCorrelationEngine:
    """
    Computes rolling correlations between gold and key cross-assets.
    Detects correlation regime shifts.
    """
    
    ASSET_LABELS = {
        "DXY": "US Dollar (DXY)",
        "US10Y": "10Y Treasury",
        "US02Y": "2Y Treasury",
        "SPY": "S&P 500 (SPY)",
        "QQQ": "Nasdaq 100 (QQQ)",
        "TLT": "Long Bonds (TLT)",
        "CrudeOil": "Crude Oil (CL)",
        "Gold": "Gold (GC)",
        "Silver": "Silver (SI)",
        "BTC": "Bitcoin (BTC)",
        "ETH": "Ethereum (ETH)",
        "VIX": "VIX",
        "GLD_ETF": "Gold ETF (GLD)",
        "SLV_ETF": "Silver ETF (SLV)",
        "Copper": "Copper (HG)",
        "Brent": "Brent (BZ)",
        "WTI": "WTI Crude (CL)",
        "Nifty50": "Nifty 50",
        "Sensex": "Sensex",
        "USDINR": "USD/INR",
    }

    def __init__(self, gold_daily: pd.DataFrame, cross_assets: dict,
                 asset_cfg: dict = None):
        self.gold = gold_daily
        self.cross = cross_assets
        self.asset_cfg = asset_cfg or {}
        self.asset_class = self.asset_cfg.get("asset_class", "metal")
        self.name = self.asset_cfg.get("name", "Gold")
    
    def analyze(self) -> dict:
        """Compute cross-asset correlation analysis."""
        result = {
            "correlations_30d": {},
            "correlations_90d": {},
            "regime": "Unknown",
            "divergences": [],
            "matrix": [],
        }
        
        if self.gold.empty or "Close" not in self.gold.columns:
            return result
        
        gold_close = self.gold["Close"].squeeze() if isinstance(self.gold["Close"], pd.DataFrame) else self.gold["Close"]
        gold_returns = gold_close.pct_change().dropna()
        
        # Compute correlations for each asset
        asset_returns = {}
        for name, df in self.cross.items():
            if df is None or (hasattr(df, 'empty') and df.empty):
                continue
            if "Close" not in df.columns:
                continue
            
            asset_close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
            asset_ret = asset_close.pct_change().dropna()
            asset_returns[name] = asset_ret
            
            # Align with gold returns
            aligned_gold, aligned_asset = gold_returns.align(asset_ret, join='inner')
            
            if len(aligned_gold) < 10:
                continue
            
            # 30-day correlation
            if len(aligned_gold) >= 30:
                corr_30d = float(aligned_gold.tail(30).corr(aligned_asset.tail(30)))
                result["correlations_30d"][name] = round(corr_30d, 4)
            
            # 90-day correlation
            if len(aligned_gold) >= 90:
                corr_90d = float(aligned_gold.tail(90).corr(aligned_asset.tail(90)))
                result["correlations_90d"][name] = round(corr_90d, 4)
            
            # Check for divergences (correlation changing sign)
            if name in result["correlations_30d"] and name in result["correlations_90d"]:
                c30 = result["correlations_30d"][name]
                c90 = result["correlations_90d"][name]
                
                if (c30 > 0.1 and c90 < -0.1) or (c30 < -0.1 and c90 > 0.1):
                    label = self.ASSET_LABELS.get(name, name)
                    result["divergences"].append({
                        "asset": label,
                        "asset_key": name,
                        "corr_30d": c30,
                        "corr_90d": c90,
                        "alert": f"Correlation flip detected: 30d={c30:.3f} vs 90d={c90:.3f}"
                    })
        
        # Build correlation matrix for heatmap
        result["matrix"] = self._build_matrix(result["correlations_30d"])
        
        # Detect regime
        result["regime"] = self._detect_regime(result["correlations_30d"])
        
        return result
    
    def _build_matrix(self, corr_dict: dict) -> list:
        """Build matrix data for frontend heatmap."""
        matrix = []
        for asset, corr in corr_dict.items():
            label = self.ASSET_LABELS.get(asset, asset)
            matrix.append({
                "asset": label,
                "asset_key": asset,
                "correlation": corr,
                "strength": self._corr_strength(corr),
            })
        
        # Sort by absolute correlation
        matrix.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return matrix
    
    def _corr_strength(self, corr: float) -> str:
        """Classify correlation strength."""
        ac = abs(corr)
        if ac > 0.7:
            return "Strong"
        elif ac > 0.4:
            return "Moderate"
        elif ac > 0.2:
            return "Weak"
        else:
            return "Negligible"
    
    def _detect_regime(self, corr_30d: dict) -> str:
        """
        Detect gold's current correlation regime:
        - "Risk-Off": Gold ↑ when SPY ↓, TLT ↑ (safe haven mode)
        - "Inflation": Gold ↑ with Oil ↑, DXY ↓ (inflation hedge mode)
        - "Dollar-Driven": Strong inverse DXY correlation
        - "Decorrelated": Gold moving independently
        """
        dxy_corr = corr_30d.get("DXY", 0)
        spy_corr = corr_30d.get("SPY", 0)
        qqq_corr = corr_30d.get("QQQ", 0)
        tlt_corr = corr_30d.get("TLT", 0)
        oil_corr = corr_30d.get("CrudeOil", 0)
        silver_corr = corr_30d.get("Silver", 0)
        btc_corr = corr_30d.get("BTC", 0)
        name = self.name

        # Risk-ON / cyclical assets (crypto, indices, stocks, commodities) —
        # frame the regime around equities/USD, not safe havens.
        if self.asset_class != "metal":
            equity_corr = max(spy_corr, qqq_corr,
                              corr_30d.get("DowJones", 0),
                              corr_30d.get("Nasdaq", 0),
                              corr_30d.get("S&P500", 0),
                              corr_30d.get("Nifty50", 0))
            if equity_corr > 0.5:
                return f"Risk-On ({name} tracking equities)"
            elif dxy_corr < -0.4:
                return f"Dollar-Driven ({name} inversely tracking USD)"
            elif self.asset_class == "crypto" and btc_corr > 0.7:
                return f"Crypto-Correlated ({name} moving with BTC)"
            elif equity_corr < -0.3:
                return f"De-Risking ({name} falling as equities weaken)"
            elif abs(dxy_corr) < 0.15 and abs(equity_corr) < 0.15:
                return f"Decorrelated ({name} moving independently)"
            else:
                return "Mixed Regime"

        if dxy_corr < -0.4:
            return f"Dollar-Driven ({name} inversely tracking USD)"
        elif spy_corr < -0.3 and tlt_corr > 0.3:
            return f"Risk-Off / Safe Haven ({name} benefiting from fear)"
        elif oil_corr > 0.4 and dxy_corr < -0.2:
            return f"Inflation Hedge ({name} tracking commodity complex)"
        elif silver_corr > 0.7:
            return f"Precious Metals Rally ({name}-Silver moving together)"
        elif abs(dxy_corr) < 0.15 and abs(spy_corr) < 0.15:
            return f"Decorrelated ({name} moving independently)"
        else:
            return "Mixed Regime"
