"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Seasonality Engine                    ║
║   Monthly, day-of-week, and day-of-month seasonal patterns       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
from datetime import datetime


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri"]


class GoldSeasonalityEngine:
    """
    Computes historical seasonal tendencies for gold using a long daily
    history. Helps frame whether the calendar is a tailwind or headwind
    for the current session.
    """

    def __init__(self, gold_long: pd.DataFrame):
        self.df = gold_long if gold_long is not None else pd.DataFrame()

    def analyze(self) -> dict:
        result = {
            "monthly": [],
            "day_of_week": [],
            "current_month": None,
            "current_dow": None,
            "summary": "Insufficient history for seasonality.",
            "years_of_data": 0,
        }

        if self.df.empty or "Close" not in self.df.columns:
            return result

        close = self.df["Close"].squeeze() if isinstance(self.df["Close"], pd.DataFrame) else self.df["Close"]
        df = pd.DataFrame({"close": close}).dropna()
        df["ret"] = df["close"].pct_change()
        df = df.dropna()
        if len(df) < 250:
            return result

        df.index = pd.to_datetime(df.index)
        result["years_of_data"] = round(len(df) / 252, 1)

        # ── Monthly seasonality: average return per calendar month ──
        df["month"] = df.index.month
        monthly = df.groupby("month")["ret"].agg(
            avg_daily="mean", pos_rate=lambda s: (s > 0).mean(), n="count"
        )
        # Aggregate to average monthly return (compounded by typical month length)
        month_total = df.groupby([df.index.year, df.index.month])["ret"].apply(
            lambda s: (1 + s).prod() - 1
        )
        month_avg = month_total.groupby(level=1).mean()
        month_winrate = month_total.groupby(level=1).apply(lambda s: (s > 0).mean())

        for m in range(1, 13):
            if m in month_avg.index:
                result["monthly"].append({
                    "month": MONTH_NAMES[m - 1],
                    "month_num": m,
                    "avg_return_pct": round(float(month_avg.loc[m]) * 100, 2),
                    "win_rate": round(float(month_winrate.loc[m]) * 100, 1),
                    "samples": int(monthly.loc[m, "n"]) if m in monthly.index else 0,
                })

        # ── Quarterly seasonality ──
        q_total = df.groupby([df.index.year, df.index.quarter])["ret"].apply(
            lambda s: (1 + s).prod() - 1
        )
        q_avg = q_total.groupby(level=1).mean()
        q_win = q_total.groupby(level=1).apply(lambda s: (s > 0).mean())
        result["quarterly"] = []
        for q in range(1, 5):
            if q in q_avg.index:
                result["quarterly"].append({
                    "quarter": f"Q{q}",
                    "quarter_num": q,
                    "avg_return_pct": round(float(q_avg.loc[q]) * 100, 2),
                    "win_rate": round(float(q_win.loc[q]) * 100, 1),
                })

        # ── Best / worst months ranking ──
        ranked = sorted(result["monthly"], key=lambda x: x["avg_return_pct"], reverse=True)
        result["best_months"] = ranked[:3]
        result["worst_months"] = ranked[-3:][::-1]

        # ── Day-of-week seasonality ──
        df["dow"] = df.index.dayofweek  # 0=Mon
        for d in range(5):
            sub = df[df["dow"] == d]["ret"]
            if len(sub) > 0:
                result["day_of_week"].append({
                    "day": DOW_NAMES[d],
                    "dow_num": d,
                    "avg_return_pct": round(float(sub.mean()) * 100, 3),
                    "win_rate": round(float((sub > 0).mean()) * 100, 1),
                    "samples": int(len(sub)),
                })

        # ── Current context ──
        now = datetime.now()
        cur_month = now.month
        cur_dow = now.weekday()
        cur_month_stat = next((x for x in result["monthly"] if x["month_num"] == cur_month), None)
        cur_dow_stat = next((x for x in result["day_of_week"] if x["dow_num"] == cur_dow), None)
        result["current_month"] = cur_month_stat
        result["current_dow"] = cur_dow_stat
        cur_q = (cur_month - 1) // 3 + 1
        result["current_quarter"] = next(
            (x for x in result.get("quarterly", []) if x["quarter_num"] == cur_q), None)

        # ── Seasonal bias summary ──
        bias_parts = []
        seasonal_score = 0
        if cur_month_stat:
            mr = cur_month_stat["avg_return_pct"]
            if mr > 0.8:
                bias_parts.append(f"{cur_month_stat['month']} is historically strong for gold (+{mr}% avg, {cur_month_stat['win_rate']}% win)")
                seasonal_score += 1
            elif mr < -0.8:
                bias_parts.append(f"{cur_month_stat['month']} is historically weak for gold ({mr}% avg, {cur_month_stat['win_rate']}% win)")
                seasonal_score -= 1
            else:
                bias_parts.append(f"{cur_month_stat['month']} is seasonally neutral ({mr:+}% avg)")
        if cur_dow_stat:
            bias_parts.append(f"{cur_dow_stat['day']} avg {cur_dow_stat['avg_return_pct']:+}% ({cur_dow_stat['win_rate']}% positive)")

        result["seasonal_score"] = seasonal_score
        result["summary"] = " · ".join(bias_parts) if bias_parts else "No clear seasonal bias."
        return result
