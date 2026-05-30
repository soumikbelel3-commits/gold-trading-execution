"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Scenario & Event-Risk Engine          ║
║   Event calendar proximity, macro betas/scenarios, gold in FX,   ║
║   pre-session risk checklist                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta


# Scheduled FOMC rate-decision days (verify against the official Fed calendar).
# Decision day = second day of each two-day meeting.
FOMC_2026 = [
    date(2026, 1, 28), date(2026, 3, 18), date(2026, 4, 29), date(2026, 6, 17),
    date(2026, 7, 29), date(2026, 9, 16), date(2026, 10, 28), date(2026, 12, 9),
]


class GoldScenarioEngine:
    """
    Forward-looking risk context: how close are we to high-impact macro
    events, how sensitive is gold to the dollar and yields right now, what
    is gold worth in other currencies, and a quick pre-session checklist.
    """

    def __init__(self, technical: dict, gold_daily: pd.DataFrame,
                 cross_assets: dict, fx: dict, macro: dict, volatility: dict):
        self.tech = technical or {}
        self.daily = gold_daily if gold_daily is not None else pd.DataFrame()
        self.cross = cross_assets or {}
        self.fx = fx or {}
        self.macro = macro or {}
        self.vol = volatility or {}

    def analyze(self) -> dict:
        return {
            "events": self._event_calendar(),
            "sensitivities": self._macro_betas(),
            "gold_in_fx": self._gold_in_currencies(),
            "checklist": self._risk_checklist(),
        }

    # ──────────────────────────────────────────────
    def _event_calendar(self) -> list:
        today = date.today()
        events = []

        # Non-Farm Payrolls — first Friday of the month
        events.append(self._mark("Non-Farm Payrolls (NFP)", self._next_first_friday(today),
                                  "High", "Big USD & gold volatility on the print"))
        # US CPI — approx 13th of the month
        events.append(self._mark("US CPI (Inflation)", self._next_day_of_month(today, 13),
                                  "High", "Inflation surprise drives real-yield repricing"))
        # FOMC rate decision
        next_fomc = next((d for d in FOMC_2026 if d >= today), None)
        if next_fomc:
            events.append(self._mark("FOMC Rate Decision", next_fomc,
                                     "Very High", "Rate path & dot-plot — largest gold driver"))
        # PCE — approx last business day window (~28th)
        events.append(self._mark("US PCE (Fed's preferred gauge)", self._next_day_of_month(today, 28),
                                  "Medium", "Confirms/denies CPI inflation trend"))

        events.sort(key=lambda e: e["days_until"])
        # Flag imminent (within 2 days) events
        for e in events:
            e["imminent"] = e["days_until"] <= 2
        return events

    def _mark(self, name, when, impact, note):
        days = (when - date.today()).days
        return {
            "event": name,
            "date": when.isoformat(),
            "date_label": when.strftime("%a %d %b"),
            "days_until": days,
            "impact": impact,
            "note": note,
        }

    @staticmethod
    def _next_first_friday(today):
        for m_off in range(0, 3):
            y = today.year + (today.month - 1 + m_off) // 12
            m = (today.month - 1 + m_off) % 12 + 1
            d = date(y, m, 1)
            d += timedelta(days=(4 - d.weekday()) % 7)  # first Friday
            if d >= today:
                return d
        return today

    @staticmethod
    def _next_day_of_month(today, dom):
        y, m = today.year, today.month
        try:
            cand = date(y, m, dom)
        except ValueError:
            cand = date(y, m, 28)
        if cand < today:
            m += 1
            if m > 12:
                m = 1
                y += 1
            cand = date(y, m, min(dom, 28))
        return cand

    # ──────────────────────────────────────────────
    def _macro_betas(self) -> dict:
        """Recent sensitivity (beta) of gold returns to DXY and 10Y yield moves."""
        result = {"scenarios": []}
        if self.daily.empty or "Close" not in self.daily.columns:
            return result
        gclose = self.daily["Close"].squeeze() if isinstance(self.daily["Close"], pd.DataFrame) else self.daily["Close"]
        gret = gclose.pct_change()

        def beta_vs(asset_key, is_yield=False):
            df = self.cross.get(asset_key)
            if df is None or (hasattr(df, "empty") and df.empty) or "Close" not in df.columns:
                return None
            aclose = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
            # yields: use change in level; price assets: pct change
            achg = aclose.diff() if is_yield else aclose.pct_change()
            g, a = gret.align(achg, join="inner")
            g, a = g.dropna().tail(60), a.dropna().tail(60)
            g, a = g.align(a, join="inner")
            if len(g) < 20 or a.var() == 0:
                return None
            beta = float(np.cov(g, a)[0, 1] / np.var(a))
            corr = float(np.corrcoef(g, a)[0, 1])
            return beta, corr

        price = self.tech.get("current_price", 0)

        dxy = beta_vs("DXY")
        if dxy:
            beta, corr = dxy
            # beta = gold %ret per 1% DXY move. Scenario: DXY +1%
            move = beta * 1.0  # for +1% DXY
            result["scenarios"].append({
                "driver": "DXY +1% (stronger USD)",
                "gold_pct": round(move, 2),
                "gold_price": round(price * (1 + move / 100), 2) if price else None,
                "corr": round(corr, 2),
            })
            result["scenarios"].append({
                "driver": "DXY -1% (weaker USD)",
                "gold_pct": round(-move, 2),
                "gold_price": round(price * (1 - move / 100), 2) if price else None,
                "corr": round(corr, 2),
            })
            result["dxy_beta"] = round(beta, 2)

        y10 = beta_vs("US10Y", is_yield=True)
        if y10:
            beta, corr = y10
            # ^TNX is yield*10 in some feeds; treat diff as index points. Scenario +10bps.
            move = beta * 0.10  # +0.10 in TNX ≈ +10bps
            result["scenarios"].append({
                "driver": "10Y yield +10bps",
                "gold_pct": round(move, 2),
                "gold_price": round(price * (1 + move / 100), 2) if price else None,
                "corr": round(corr, 2),
            })
            result["yield_beta"] = round(beta, 3)

        spy = beta_vs("SPY")
        if spy:
            beta, corr = spy
            move = beta * -2.0  # equities sell off 2%
            result["scenarios"].append({
                "driver": "Risk-off: S&P 500 −2%",
                "gold_pct": round(move, 2),
                "gold_price": round(price * (1 + move / 100), 2) if price else None,
                "corr": round(corr, 2),
            })

        vix = beta_vs("VIX")
        if vix:
            beta, corr = vix
            move = beta * 20.0  # VIX spikes +20%
            result["scenarios"].append({
                "driver": "Fear spike: VIX +20%",
                "gold_pct": round(move, 2),
                "gold_price": round(price * (1 + move / 100), 2) if price else None,
                "corr": round(corr, 2),
            })

        return result

    # ──────────────────────────────────────────────
    def _gold_in_currencies(self) -> list:
        price = self.tech.get("current_price")
        if not price:
            return []
        out = [{"currency": "USD", "symbol": "$", "price": round(price, 2), "per": "oz"}]
        eur = self.fx.get("EURUSD")
        if eur:
            out.append({"currency": "EUR", "symbol": "€", "price": round(price / eur, 2), "per": "oz"})
        jpy = self.fx.get("USDJPY")
        if jpy:
            out.append({"currency": "JPY", "symbol": "¥", "price": round(price * jpy, 0), "per": "oz"})
        gbp = self.fx.get("GBPUSD")
        if gbp:
            out.append({"currency": "GBP", "symbol": "£", "price": round(price / gbp, 2), "per": "oz"})
        return out

    # ──────────────────────────────────────────────
    def _risk_checklist(self) -> list:
        checks = []
        # Event proximity
        events = self._event_calendar()
        imminent = [e for e in events if e["imminent"]]
        if imminent:
            names = ", ".join(e["event"] for e in imminent)
            checks.append({"status": "warn", "text": f"High-impact event within 48h: {names} — size down / widen stops"})
        else:
            checks.append({"status": "ok", "text": "No top-tier macro event in the next 48 hours"})

        # Volatility regime
        regime = self.vol.get("regime", "")
        if "Extreme" in regime or "High" in regime:
            checks.append({"status": "warn", "text": f"{regime} — expect larger ranges, use wider stops"})
        elif "Low" in regime:
            checks.append({"status": "ok", "text": f"{regime} — tighter ranges, breakout risk if vol expands"})
        else:
            checks.append({"status": "ok", "text": f"Volatility regime: {regime or 'Normal'}"})

        # Vol percentile extreme
        pctl = self.vol.get("vol_percentile")
        if pctl is not None and pctl > 80:
            checks.append({"status": "warn", "text": f"Volatility at {pctl:.0f}th percentile — elevated, mean-reversion risk"})
        elif pctl is not None and pctl < 20:
            checks.append({"status": "warn", "text": f"Volatility at {pctl:.0f}th percentile — compression, breakout setup likely"})

        # Macro alignment
        regime_m = self.macro.get("regime", "")
        checks.append({"status": "ok", "text": f"Macro backdrop: {regime_m or 'Neutral'}"})

        return checks
