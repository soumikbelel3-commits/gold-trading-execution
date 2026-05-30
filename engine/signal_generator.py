"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Signal Generator                      ║
║   Composite alpha signal from all analysis modules               ║
╚══════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from datetime import datetime


class GoldSignalGenerator:
    """
    Produces a composite trading signal by combining:
    - Technical analysis score
    - Macro environment score
    - Sentiment score
    - Volatility regime
    - Cross-asset correlations
    
    Output: Signal strength (-1 to +1), confidence (0 to 1), regime label
    """
    
    # Base weights when no ML is available
    WEIGHTS = {
        "technical": 0.28,
        "macro": 0.22,
        "sentiment": 0.12,
        "volatility": 0.10,
        "correlation": 0.13,
        "ml": 0.10,
        "seasonality": 0.05,
    }

    def generate(self, technical: dict, macro: dict, sentiment: dict,
                 volatility: dict, correlation: dict,
                 pipeline_signals: dict = None,
                 ml: dict = None, seasonality: dict = None) -> dict:
        """
        Generate composite signal from all analysis results.
        
        Returns dict with:
            signal: float (-1 to +1)
            confidence: float (0 to 1)
            regime: str
            breakdown: dict of component signals
            action: str (recommendation)
        """
        breakdown = {}
        
        # ── Technical Score → Normalized to [-1, +1] ──
        tech_score = technical.get("overall_score", 0)
        # Raw score is roughly -5 to +5, normalize
        tech_normalized = np.clip(tech_score / 5, -1, 1)
        breakdown["technical"] = {
            "raw": tech_score,
            "normalized": round(tech_normalized, 4),
            "bias": technical.get("overall_bias", "Neutral"),
            "weight": self.WEIGHTS["technical"],
        }
        
        # ── Macro Score → Normalized ──
        macro_score = macro.get("composite_score", 0)
        max_score = macro.get("max_possible", 18)
        macro_normalized = np.clip(macro_score / max_score * 2, -1, 1)
        breakdown["macro"] = {
            "raw": macro_score,
            "normalized": round(macro_normalized, 4),
            "regime": macro.get("regime", "Neutral"),
            "weight": self.WEIGHTS["macro"],
        }
        
        # ── Sentiment Score ──
        sent_score = sentiment.get("composite_score", 0)
        # Already in [-1, +1] range
        sent_normalized = np.clip(sent_score, -1, 1)
        breakdown["sentiment"] = {
            "raw": sent_score,
            "normalized": round(sent_normalized, 4),
            "label": sentiment.get("composite_label", "Neutral"),
            "weight": self.WEIGHTS["sentiment"],
        }
        
        # ── Volatility Score ──
        vol_score = volatility.get("vol_score", 0)
        vol_normalized = np.clip(vol_score / 3, -1, 1)
        breakdown["volatility"] = {
            "raw": vol_score,
            "normalized": round(vol_normalized, 4),
            "regime": volatility.get("regime", "Normal"),
            "weight": self.WEIGHTS["volatility"],
        }
        
        # ── Correlation Score ──
        # Use DXY inverse + regime as signal
        corr_30d = correlation.get("correlations_30d", {})
        dxy_corr = corr_30d.get("DXY", 0)
        spy_corr = corr_30d.get("SPY", 0)
        # If gold is inversely correlated with DXY (normal), and DXY is weak → bullish
        corr_signal = -dxy_corr * 0.5 + (0.3 if correlation.get("regime", "").startswith("Risk-Off") else 0)
        corr_normalized = np.clip(corr_signal, -1, 1)
        breakdown["correlation"] = {
            "raw": round(corr_signal, 4),
            "normalized": round(corr_normalized, 4),
            "regime": correlation.get("regime", "Mixed"),
            "weight": self.WEIGHTS["correlation"],
        }

        # ── ML Score → prob_up centered to [-1, +1] ──
        if ml and ml.get("available") and ml.get("prediction"):
            prob_up = ml["prediction"].get("prob_up", 50)
            ml_normalized = np.clip((prob_up - 50) / 50, -1, 1)
            breakdown["ml"] = {
                "raw": prob_up,
                "normalized": round(float(ml_normalized), 4),
                "regime": f"{ml['prediction'].get('direction', '?')} {prob_up}%",
                "weight": self.WEIGHTS["ml"],
            }

        # ── Seasonality Score ──
        if seasonality and seasonality.get("seasonal_score") is not None:
            seas = seasonality.get("seasonal_score", 0)
            seas_normalized = np.clip(seas, -1, 1)
            breakdown["seasonality"] = {
                "raw": seas,
                "normalized": round(float(seas_normalized), 4),
                "regime": (seasonality.get("current_month") or {}).get("month", "N/A"),
                "weight": self.WEIGHTS["seasonality"],
            }

        # ── Composite Signal (weights renormalized over present components) ──
        weighted_sum = 0
        total_weight = 0
        for key, weight in self.WEIGHTS.items():
            if key in breakdown:
                weighted_sum += breakdown[key]["normalized"] * weight
                total_weight += weight
        
        composite = weighted_sum / total_weight if total_weight > 0 else 0
        composte_clipped = np.clip(composite, -1, 1)
        
        # ── Confidence ──
        # Higher confidence when signals agree
        signals = [breakdown[k]["normalized"] for k in breakdown]
        if signals:
            std_dev = np.std(signals)
            # Low std = high agreement = high confidence
            agreement = max(0, 1 - std_dev)
            signal_strength = abs(composte_clipped)
            confidence = (agreement * 0.6 + signal_strength * 0.4)
        else:
            confidence = 0
        
        # ── Pipeline Signal Integration ──
        if pipeline_signals and "composite_signal" in pipeline_signals:
            ps = pipeline_signals["composite_signal"]
            breakdown["pipeline"] = {
                "signal": ps,
                "regime": pipeline_signals.get("regime", "N/A"),
                "confidence": pipeline_signals.get("confidence", 0),
            }
        
        # ── Action Recommendation ──
        signal = round(composte_clipped, 4)
        if signal > 0.4:
            action = "STRONG BUY"
            emoji = "🟢🟢"
        elif signal > 0.2:
            action = "BUY"
            emoji = "🟢"
        elif signal > 0.05:
            action = "SLIGHT BUY BIAS"
            emoji = "🟡↑"
        elif signal > -0.05:
            action = "NEUTRAL"
            emoji = "⚪"
        elif signal > -0.2:
            action = "SLIGHT SELL BIAS"
            emoji = "🟡↓"
        elif signal > -0.4:
            action = "SELL"
            emoji = "🔴"
        else:
            action = "STRONG SELL"
            emoji = "🔴🔴"
        
        # ── Regime Classification ──
        if signal > 0.3:
            regime = "STRONG BULLISH"
        elif signal > 0.1:
            regime = "BULLISH"
        elif signal > -0.1:
            regime = "NEUTRAL"
        elif signal > -0.3:
            regime = "BEARISH"
        else:
            regime = "STRONG BEARISH"
        
        return {
            "signal": signal,
            "confidence": round(confidence, 4),
            "regime": regime,
            "action": action,
            "emoji": emoji,
            "breakdown": breakdown,
            "timestamp": datetime.now().isoformat(),
        }
