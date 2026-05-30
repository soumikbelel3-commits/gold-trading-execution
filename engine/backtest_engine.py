"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Signal Backtest Engine                ║
║   Historical edge of technical rules + composite-score regimes   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np


class GoldBacktestEngine:
    """
    Quantifies the historical edge of the technical rules used elsewhere
    in the dashboard. For each rule we measure the forward N-day return
    distribution when the rule was true, versus the unconditional baseline.
    Also backtests a daily composite technical-score strategy.
    """

    def __init__(self, gold_long: pd.DataFrame, horizon: int = 5):
        self.df = gold_long if gold_long is not None else pd.DataFrame()
        self.horizon = horizon

    def analyze(self) -> dict:
        result = {"available": False, "rules": [], "baseline": {}, "strategy": {}}
        if self.df.empty or "Close" not in self.df.columns or len(self.df) < 250:
            return result

        df = self._prepare()
        if df is None:
            return result

        fwd = df["fwd_ret"]
        result["baseline"] = self._stats(fwd)
        result["horizon_days"] = self.horizon
        result["available"] = True

        rules = {
            "RSI < 30 (Oversold)": df["rsi"] < 30,
            "RSI > 70 (Overbought)": df["rsi"] > 70,
            "Golden Cross (50>200)": df["sma50"] > df["sma200"],
            "Price > SMA200": df["close"] > df["sma200"],
            "MACD Bullish": df["macd"] > df["macd_sig"],
            "Below Lower Bollinger": df["close"] < df["bb_lower"],
            "Above Upper Bollinger": df["close"] > df["bb_upper"],
        }

        base_mean = result["baseline"]["avg_return_pct"]
        for name, mask in rules.items():
            sub = fwd[mask].dropna()
            if len(sub) < 20:
                continue
            s = self._stats(sub)
            s["rule"] = name
            s["edge_vs_baseline_pct"] = round(s["avg_return_pct"] - base_mean, 3)
            result["rules"].append(s)

        result["rules"].sort(key=lambda x: x["edge_vs_baseline_pct"], reverse=True)

        # ── Composite technical-score strategy backtest ──
        result["strategy"] = self._backtest_strategy(df)
        return result

    def _prepare(self):
        close = self.df["Close"].squeeze() if isinstance(self.df["Close"], pd.DataFrame) else self.df["Close"]
        high = self.df["High"].squeeze() if "High" in self.df.columns else close
        low = self.df["Low"].squeeze() if "Low" in self.df.columns else close
        df = pd.DataFrame({"close": close, "high": high, "low": low}).dropna()
        if len(df) < 250:
            return None

        df["ret"] = df["close"].pct_change()
        df["fwd_ret"] = (df["close"].shift(-self.horizon) / df["close"] - 1) * 100

        # RSI
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta).where(delta < 0, 0.0).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))

        df["sma50"] = df["close"].rolling(50).mean()
        df["sma200"] = df["close"].rolling(200).mean()

        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()
        df["macd"] = ema12 - ema26
        df["macd_sig"] = df["macd"].ewm(span=9).mean()

        bb_sma = df["close"].rolling(20).mean()
        bb_std = df["close"].rolling(20).std()
        df["bb_upper"] = bb_sma + 2 * bb_std
        df["bb_lower"] = bb_sma - 2 * bb_std

        # Composite "score" proxy used by the live technical analyzer
        score = pd.Series(0.0, index=df.index)
        score += np.where(df["close"] > df["sma50"], 0.5, -0.5)
        score += np.where(df["close"] > df["sma200"], 0.5, -0.5)
        score += np.where(df["sma50"] > df["sma200"], 1.0, -1.0)
        score += np.where(df["macd"] > df["macd_sig"], 1.0, -1.0)
        score += np.where(df["rsi"] > 55, 0.5, np.where(df["rsi"] < 45, -0.5, 0))
        df["score"] = score
        return df.dropna(subset=["sma200", "rsi"])

    def _backtest_strategy(self, df: pd.DataFrame) -> dict:
        """Go long next day when composite score is bullish; flat otherwise."""
        d = df.dropna(subset=["score", "ret"]).copy()
        if len(d) < 100:
            return {}
        # Position decided on prior close, applied to today's return
        d["pos"] = np.where(d["score"].shift(1) >= 1.0, 1.0, 0.0)
        d["strat_ret"] = d["pos"] * d["ret"]

        def curve_stats(rets):
            equity = (1 + rets.fillna(0)).cumprod()
            total = float(equity.iloc[-1] - 1) * 100
            ann = float((1 + rets.mean()) ** 252 - 1) * 100
            vol = float(rets.std() * np.sqrt(252)) * 100
            sharpe = round(ann / vol, 2) if vol > 0 else 0.0
            dd = float(((equity / equity.cummax()) - 1).min()) * 100
            return total, ann, sharpe, dd

        s_total, s_ann, s_sharpe, s_dd = curve_stats(d["strat_ret"])
        b_total, b_ann, b_sharpe, b_dd = curve_stats(d["ret"])

        # Downsampled equity curve for charting
        eq = (1 + d["strat_ret"].fillna(0)).cumprod()
        bh = (1 + d["ret"].fillna(0)).cumprod()
        step = max(1, len(eq) // 250)
        curve = [{
            "t": int(pd.Timestamp(idx).timestamp()),
            "strat": round(float(eq.iloc[i]), 4),
            "bh": round(float(bh.iloc[i]), 4),
        } for i, idx in enumerate(eq.index) if i % step == 0]

        return {
            "description": "Long gold when composite technical score is bullish (score>=1), else flat.",
            "strategy": {
                "total_return_pct": round(s_total, 1),
                "annual_return_pct": round(s_ann, 1),
                "sharpe": s_sharpe,
                "max_drawdown_pct": round(s_dd, 1),
                "time_in_market_pct": round(float(d["pos"].mean()) * 100, 1),
            },
            "buy_hold": {
                "total_return_pct": round(b_total, 1),
                "annual_return_pct": round(b_ann, 1),
                "sharpe": b_sharpe,
                "max_drawdown_pct": round(b_dd, 1),
            },
            "equity_curve": curve,
        }

    @staticmethod
    def _stats(fwd: pd.Series) -> dict:
        fwd = fwd.dropna()
        return {
            "samples": int(len(fwd)),
            "avg_return_pct": round(float(fwd.mean()), 3),
            "median_return_pct": round(float(fwd.median()), 3),
            "win_rate": round(float((fwd > 0).mean()) * 100, 1),
            "best_pct": round(float(fwd.max()), 2),
            "worst_pct": round(float(fwd.min()), 2),
        }
