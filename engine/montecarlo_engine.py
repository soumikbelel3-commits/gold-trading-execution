"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Monte Carlo Projection                ║
║   Simulates next-session price distribution from current vol     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np


class GoldMonteCarloEngine:
    """
    Projects the next trading session's price range using a Monte Carlo
    simulation calibrated to recent daily log-return statistics. Produces
    probability-weighted price levels and the odds of touching key targets.
    """

    def __init__(self, gold_daily: pd.DataFrame, n_sims: int = 20000,
                 horizon_days: int = 1):
        self.df = gold_daily if gold_daily is not None else pd.DataFrame()
        self.n_sims = n_sims
        self.horizon = horizon_days

    def analyze(self) -> dict:
        result = {"available": False}
        if self.df.empty or "Close" not in self.df.columns:
            return result

        close = self.df["Close"].squeeze() if isinstance(self.df["Close"], pd.DataFrame) else self.df["Close"]
        close = close.dropna()
        if len(close) < 60:
            return result

        log_ret = np.log(close / close.shift(1)).dropna()
        # Use the last 60 sessions to capture the prevailing regime
        recent = log_ret.tail(60)
        mu = float(recent.mean())
        sigma = float(recent.std())
        spot = float(close.iloc[-1])

        if sigma <= 0 or not np.isfinite(sigma):
            return result

        rng = np.random.default_rng(42)
        # Aggregate horizon drift/vol
        total_mu = mu * self.horizon
        total_sigma = sigma * np.sqrt(self.horizon)
        shocks = rng.normal(total_mu, total_sigma, self.n_sims)
        sim_prices = spot * np.exp(shocks)

        pct = lambda q: round(float(np.percentile(sim_prices, q)), 2)
        result.update({
            "available": True,
            "spot": round(spot, 2),
            "horizon_days": self.horizon,
            "n_sims": self.n_sims,
            "daily_vol_pct": round(sigma * 100, 3),
            "annualized_vol_pct": round(sigma * np.sqrt(252) * 100, 2),
            "drift_bps": round(mu * 10000, 2),
            "percentiles": {
                "p5": pct(5), "p25": pct(25), "p50": pct(50),
                "p75": pct(75), "p95": pct(95),
            },
            "expected_move_pct": round(total_sigma * 100, 3),
            "prob_up": round(float((sim_prices > spot).mean()) * 100, 1),
        })

        # Probability of touching round/ATR-style targets
        moves = [0.005, 0.01, 0.015, 0.02]
        touch = []
        for m in moves:
            up_level = spot * (1 + m)
            dn_level = spot * (1 - m)
            touch.append({
                "move_pct": round(m * 100, 1),
                "up_level": round(up_level, 2),
                "dn_level": round(dn_level, 2),
                "prob_up_close": round(float((sim_prices >= up_level).mean()) * 100, 1),
                "prob_dn_close": round(float((sim_prices <= dn_level).mean()) * 100, 1),
            })
        result["target_probabilities"] = touch

        # 1-standard-deviation expected band
        result["expected_band"] = {
            "low": round(spot * np.exp(total_mu - total_sigma), 2),
            "high": round(spot * np.exp(total_mu + total_sigma), 2),
        }

        # Build a coarse histogram for the frontend
        counts, edges = np.histogram(sim_prices, bins=40)
        result["histogram"] = {
            "counts": counts.tolist(),
            "edges": [round(float(e), 2) for e in edges],
        }
        return result
