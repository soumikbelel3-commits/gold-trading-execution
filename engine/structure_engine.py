"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Market Structure Engine               ║
║   S/R confluence zones, candlestick patterns, ADX, VWAP,         ║
║   Gold/Silver ratio                                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np


class GoldStructureEngine:
    """
    Higher-order market-structure analysis built on top of the technical
    indicators: clusters raw levels into high-probability confluence zones,
    detects recent candlestick patterns, measures trend strength (ADX),
    computes session VWAP, and tracks the Gold/Silver ratio.
    """

    def __init__(self, gold_daily: pd.DataFrame, gold_1h: pd.DataFrame,
                 technical: dict, cross_assets: dict = None):
        self.daily = gold_daily if gold_daily is not None else pd.DataFrame()
        self.h1 = gold_1h if gold_1h is not None else pd.DataFrame()
        self.tech = technical or {}
        self.cross = cross_assets or {}

    def analyze(self) -> dict:
        return {
            "confluence_zones": self._confluence_zones(),
            "patterns": self._candlestick_patterns(),
            "adx": self._adx(),
            "vwap": self._vwap(),
            "gold_silver_ratio": self._gold_silver_ratio(),
            "swing_structure": self._swing_structure(),
        }

    # ──────────────────────────────────────────────
    def _swing_structure(self) -> dict:
        """Classify market structure from recent swing highs/lows (HH/HL vs LH/LL)."""
        if self.daily.empty or len(self.daily) < 25:
            return {}
        df = self.daily.tail(60)
        high = df["High"].squeeze() if "High" in df.columns else df["Close"]
        low = df["Low"].squeeze() if "Low" in df.columns else df["Close"]
        close = df["Close"].squeeze()

        # Two halves for swing comparison
        n = len(df)
        h_recent = float(high.tail(n // 3).max())
        h_prev = float(high.iloc[n // 3: 2 * n // 3].max())
        l_recent = float(low.tail(n // 3).min())
        l_prev = float(low.iloc[n // 3: 2 * n // 3].min())

        hh = h_recent > h_prev
        hl = l_recent > l_prev
        if hh and hl:
            label, bias = "Uptrend (Higher Highs & Higher Lows)", "Bullish"
        elif not hh and not hl:
            label, bias = "Downtrend (Lower Highs & Lower Lows)", "Bearish"
        elif hh and not hl:
            label, bias = "Broadening / Volatile range", "Neutral"
        else:
            label, bias = "Contracting / Coiling range", "Neutral"

        cur = float(close.iloc[-1])
        rng_pos = (cur - l_recent) / (h_recent - l_recent) * 100 if h_recent > l_recent else 50
        return {
            "label": label,
            "bias": bias,
            "recent_high": round(h_recent, 2),
            "recent_low": round(l_recent, 2),
            "range_position_pct": round(rng_pos, 1),
        }

    # ──────────────────────────────────────────────
    def _confluence_zones(self) -> list:
        """Cluster pivots, fib levels, MAs and key levels into zones."""
        price = self.tech.get("current_price")
        if not price:
            return []

        candidates = []
        pivots = self.tech.get("pivot_points", {}).get("classic", {})
        for k, v in pivots.items():
            if v:
                candidates.append((v, f"Pivot {k}"))
        fib = self.tech.get("fibonacci", {})
        fib_labels = {"fib_236": "Fib 23.6%", "fib_382": "Fib 38.2%", "fib_500": "Fib 50%",
                      "fib_618": "Fib 61.8%", "fib_786": "Fib 78.6%"}
        for k, label in fib_labels.items():
            if fib.get(k):
                candidates.append((fib[k], label))
        kl = self.tech.get("key_levels", {})
        for k, label in [("resistance_1", "20d High"), ("support_1", "20d Low"),
                         ("52w_high", "52w High"), ("52w_low", "52w Low")]:
            if kl.get(k):
                candidates.append((kl[k], label))
        daily_tf = self.tech.get("timeframes", {}).get("daily", {}).get("indicators", {})
        for ma in ["SMA_20", "SMA_50", "SMA_200", "EMA_20", "EMA_50"]:
            if daily_tf.get(ma):
                candidates.append((daily_tf[ma], ma.replace("_", " ")))

        if not candidates:
            return []

        # Cluster levels within 0.4% of each other
        tol = price * 0.004
        candidates.sort(key=lambda x: x[0])
        clusters = []
        cur = [candidates[0]]
        for lvl, lbl in candidates[1:]:
            if lvl - cur[-1][0] <= tol:
                cur.append((lvl, lbl))
            else:
                clusters.append(cur)
                cur = [(lvl, lbl)]
        clusters.append(cur)

        zones = []
        for c in clusters:
            lvls = [x[0] for x in c]
            center = float(np.mean(lvls))
            zones.append({
                "center": round(center, 2),
                "low": round(min(lvls), 2),
                "high": round(max(lvls), 2),
                "strength": len(c),
                "sources": [x[1] for x in c],
                "side": "resistance" if center > price else "support",
                "dist_pct": round((center - price) / price * 100, 2),
            })

        # Strongest zones first, but keep nearest meaningful ones
        zones = [z for z in zones if z["strength"] >= 2]
        zones.sort(key=lambda z: (-z["strength"], abs(z["dist_pct"])))
        return zones[:6]

    # ──────────────────────────────────────────────
    def _candlestick_patterns(self) -> list:
        if self.daily.empty or len(self.daily) < 5:
            return []
        df = self.daily.tail(10).copy()
        o = df["Open"].squeeze() if "Open" in df.columns else df["Close"]
        h = df["High"].squeeze() if "High" in df.columns else df["Close"]
        l = df["Low"].squeeze() if "Low" in df.columns else df["Close"]
        c = df["Close"].squeeze()
        o, h, l, c = [pd.Series(x).reset_index(drop=True) for x in (o, h, l, c)]

        patterns = []
        i = len(c) - 1

        def body(j): return abs(c[j] - o[j])
        def rng(j): return max(h[j] - l[j], 1e-9)
        def upper_wick(j): return h[j] - max(c[j], o[j])
        def lower_wick(j): return min(c[j], o[j]) - l[j]

        # Doji
        if body(i) <= 0.1 * rng(i):
            patterns.append({"name": "Doji", "bias": "Neutral",
                             "note": "Indecision — potential reversal/continuation pause"})
        # Hammer / Hanging man
        if lower_wick(i) > 2 * body(i) and upper_wick(i) < body(i):
            patterns.append({"name": "Hammer / Pin Bar", "bias": "Bullish",
                             "note": "Long lower wick — buyers rejected lows"})
        # Shooting star
        if upper_wick(i) > 2 * body(i) and lower_wick(i) < body(i):
            patterns.append({"name": "Shooting Star", "bias": "Bearish",
                             "note": "Long upper wick — sellers rejected highs"})
        # Bullish / Bearish engulfing
        if i >= 1:
            if c[i] > o[i] and c[i - 1] < o[i - 1] and c[i] >= o[i - 1] and o[i] <= c[i - 1]:
                patterns.append({"name": "Bullish Engulfing", "bias": "Bullish",
                                 "note": "Current candle engulfs prior down candle"})
            if c[i] < o[i] and c[i - 1] > o[i - 1] and o[i] >= c[i - 1] and c[i] <= o[i - 1]:
                patterns.append({"name": "Bearish Engulfing", "bias": "Bearish",
                                 "note": "Current candle engulfs prior up candle"})
        # Marubozu-ish strong candle
        if body(i) > 0.85 * rng(i):
            patterns.append({"name": "Strong Trend Candle", "bias": "Bullish" if c[i] > o[i] else "Bearish",
                             "note": "Full-body candle — strong conviction"})

        if not patterns:
            patterns.append({"name": "No major pattern", "bias": "Neutral",
                             "note": "Recent candles show no notable formation"})
        return patterns

    # ──────────────────────────────────────────────
    def _adx(self, period: int = 14) -> dict:
        if self.daily.empty or len(self.daily) < period * 2:
            return {}
        h = self.daily["High"].squeeze() if "High" in self.daily.columns else self.daily["Close"]
        l = self.daily["Low"].squeeze() if "Low" in self.daily.columns else self.daily["Close"]
        c = self.daily["Close"].squeeze()

        up = h.diff()
        dn = -l.diff()
        plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
        minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        plus_di = 100 * pd.Series(plus_dm, index=h.index).rolling(period).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=h.index).rolling(period).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(period).mean()

        adx_val = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None
        if adx_val is None:
            return {}
        if adx_val > 40:
            strength = "Very Strong Trend"
        elif adx_val > 25:
            strength = "Trending"
        elif adx_val > 20:
            strength = "Developing Trend"
        else:
            strength = "Ranging / No Trend"
        direction = "Bullish" if float(plus_di.iloc[-1]) > float(minus_di.iloc[-1]) else "Bearish"
        return {
            "adx": round(adx_val, 1),
            "plus_di": round(float(plus_di.iloc[-1]), 1),
            "minus_di": round(float(minus_di.iloc[-1]), 1),
            "strength": strength,
            "direction": direction,
        }

    # ──────────────────────────────────────────────
    def _vwap(self) -> dict:
        """Rolling VWAP over the most recent ~5 sessions of 1H data."""
        if self.h1.empty or "Volume" not in self.h1.columns:
            return {}
        df = self.h1.tail(120).copy()
        h = df["High"].squeeze() if "High" in df.columns else df["Close"]
        l = df["Low"].squeeze() if "Low" in df.columns else df["Close"]
        c = df["Close"].squeeze()
        v = df["Volume"].squeeze()
        tp = (h + l + c) / 3
        if float(v.sum()) <= 0:
            return {}
        vwap = float((tp * v).sum() / v.sum())
        price = float(c.iloc[-1])
        return {
            "vwap": round(vwap, 2),
            "price": round(price, 2),
            "position": "Above VWAP (bullish intraday)" if price > vwap else "Below VWAP (bearish intraday)",
            "dist_pct": round((price - vwap) / vwap * 100, 3),
        }

    # ──────────────────────────────────────────────
    def _gold_silver_ratio(self) -> dict:
        silver = self.cross.get("Silver")
        gold_price = self.tech.get("current_price")
        if silver is None or (hasattr(silver, "empty") and silver.empty) or not gold_price:
            return {}
        try:
            sclose = silver["Close"].squeeze() if isinstance(silver["Close"], pd.DataFrame) else silver["Close"]
            sclose = sclose.dropna()
            silver_price = float(sclose.iloc[-1])
            if silver_price <= 0:
                return {}
            ratio = gold_price / silver_price
            # Historical ratio context (rough long-run norms)
            if ratio > 90:
                regime = "Silver historically cheap vs gold (ratio extended high)"
            elif ratio > 80:
                regime = "Elevated — gold favored over silver"
            elif ratio > 65:
                regime = "Normal range"
            else:
                regime = "Low — silver favored / risk-on metals"
            # 90-day average for context
            avg90 = None
            if not silver.empty and gold_price:
                pass
            return {
                "ratio": round(ratio, 1),
                "silver_price": round(silver_price, 2),
                "regime": regime,
            }
        except Exception:
            return {}
