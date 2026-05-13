"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Session Planner                       ║
║   Trading session gameplan with MCX India support                 ║
╚══════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from datetime import datetime, timezone, timedelta


class GoldSessionPlanner:
    """
    Generates session-specific trading gameplans.
    
    Sessions:
    - Asian/MCX: 09:00–17:00 IST (03:30–11:30 UTC)
    - London: 08:00–16:30 GMT (08:00–16:30 UTC)
    - New York/COMEX: 08:20–13:30 EST (13:20–18:30 UTC)
    
    MCX Gold: 09:00–23:30 IST
    """
    
    SESSIONS = {
        "Asian / MCX": {
            "start_utc": 3.5,   # 09:00 IST = 03:30 UTC
            "end_utc": 11.5,    # 17:00 IST = 11:30 UTC
            "characteristics": [
                "Typically lower liquidity, tighter ranges",
                "China/India physical demand can drive moves",
                "Often sets the daily low or high",
                "MCX Gold tracks COMEX with INR overlay",
            ],
            "volatility_rank": "Low-Medium",
        },
        "London": {
            "start_utc": 8,
            "end_utc": 16.5,
            "characteristics": [
                "Highest liquidity session for gold",
                "London Gold Fix at 10:30 AM / 3:00 PM GMT",
                "Often sees breakout from Asian range",
                "Institutional flow dominates",
            ],
            "volatility_rank": "High",
        },
        "New York / COMEX": {
            "start_utc": 13.33,
            "end_utc": 18.5,
            "characteristics": [
                "COMEX futures dominate price discovery",
                "US economic data releases drive volatility",
                "Fed speakers can create sharp moves",
                "Options expiry effects near session end",
            ],
            "volatility_rank": "High",
        },
    }
    
    def __init__(self, technical: dict, macro: dict, volatility: dict,
                 composite_signal: dict, mcx_data: dict = None):
        self.technical = technical
        self.macro = macro
        self.volatility = volatility
        self.signal = composite_signal
        self.mcx_data = mcx_data or {}
    
    def plan(self) -> dict:
        """Generate complete session gameplan."""
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour + now_utc.minute / 60
        
        result = {
            "current_time_utc": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
            "current_time_ist": (now_utc + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M IST"),
            "active_session": self._get_active_session(current_hour),
            "next_session": self._get_next_session(current_hour),
            "sessions": {},
            "mcx_gameplan": {},
            "risk_parameters": {},
            "trade_setups": [],
        }
        
        # Build gameplan for each session
        for session_name, session_info in self.SESSIONS.items():
            result["sessions"][session_name] = self._build_session_plan(
                session_name, session_info
            )
        
        # MCX-specific gameplan
        result["mcx_gameplan"] = self._build_mcx_plan()
        
        # Risk parameters
        result["risk_parameters"] = self._compute_risk_params()
        
        # Trade setups
        result["trade_setups"] = self._generate_trade_setups()
        
        return result
    
    def _get_active_session(self, hour_utc: float) -> str:
        """Determine which session is currently active."""
        for name, info in self.SESSIONS.items():
            if info["start_utc"] <= hour_utc <= info["end_utc"]:
                return name
        return "Off-Hours"
    
    def _get_next_session(self, hour_utc: float) -> dict:
        """Determine the next upcoming session."""
        sessions_ordered = [
            ("Asian / MCX", 3.5),
            ("London", 8),
            ("New York / COMEX", 13.33),
        ]
        
        for name, start in sessions_ordered:
            if hour_utc < start:
                hours_until = start - hour_utc
                return {"name": name, "hours_until": round(hours_until, 1)}
        
        # Wrap around to next day Asian
        hours_until = (24 - hour_utc) + 3.5
        return {"name": "Asian / MCX (tomorrow)", "hours_until": round(hours_until, 1)}
    
    def _build_session_plan(self, name: str, info: dict) -> dict:
        """Build gameplan for a specific session."""
        plan = {
            "characteristics": info["characteristics"],
            "volatility_rank": info["volatility_rank"],
            "bias": "Neutral",
            "key_levels": [],
            "strategy": "",
        }
        
        signal_val = self.signal.get("signal", 0)
        current_price = self.technical.get("current_price", 0)
        
        # Session-specific bias
        if name == "Asian / MCX":
            # Asian tends to be range-bound
            if abs(signal_val) > 0.3:
                plan["bias"] = "Follow overnight momentum"
                plan["strategy"] = "Range trade within Asian session boundaries"
            else:
                plan["bias"] = "Range-bound expected"
                plan["strategy"] = "Trade S/R levels with tight stops"
        
        elif name == "London":
            # London often breaks the Asian range
            if signal_val > 0.15:
                plan["bias"] = "Bullish — look for Asian high breakout"
                plan["strategy"] = "Buy breakout above Asian session high, target R1"
            elif signal_val < -0.15:
                plan["bias"] = "Bearish — look for Asian low breakdown"
                plan["strategy"] = "Sell breakdown below Asian session low, target S1"
            else:
                plan["bias"] = "Neutral — wait for direction"
                plan["strategy"] = "Wait for clear breakout/breakdown of Asian range"
        
        elif name == "New York / COMEX":
            # NY driven by data releases
            if signal_val > 0.2:
                plan["bias"] = "Bullish — buy dips toward London session support"
                plan["strategy"] = "Buy pullbacks to London session VWAP area"
            elif signal_val < -0.2:
                plan["bias"] = "Bearish — sell rallies into London session resistance"
                plan["strategy"] = "Sell rallies into London session high area"
            else:
                plan["bias"] = "Data-dependent — trade the number"
                plan["strategy"] = "Wait for US economic data, trade the reaction"
        
        # Key levels from technical analysis
        pivots = self.technical.get("pivot_points", {}).get("classic", {})
        fib = self.technical.get("fibonacci", {})
        
        levels = []
        if pivots:
            levels.append({"level": pivots.get("R2"), "label": "R2 (Strong Resistance)", "type": "resistance"})
            levels.append({"level": pivots.get("R1"), "label": "R1 (Resistance)", "type": "resistance"})
            levels.append({"level": pivots.get("PP"), "label": "Pivot Point", "type": "pivot"})
            levels.append({"level": pivots.get("S1"), "label": "S1 (Support)", "type": "support"})
            levels.append({"level": pivots.get("S2"), "label": "S2 (Strong Support)", "type": "support"})
        
        if fib:
            levels.append({"level": fib.get("fib_382"), "label": "Fib 38.2%", "type": "fib"})
            levels.append({"level": fib.get("fib_500"), "label": "Fib 50.0%", "type": "fib"})
            levels.append({"level": fib.get("fib_618"), "label": "Fib 61.8%", "type": "fib"})
        
        plan["key_levels"] = [l for l in levels if l.get("level") is not None]
        
        return plan
    
    def _build_mcx_plan(self) -> dict:
        """Build MCX Gold specific gameplan."""
        mcx_plan = {
            "session_times": "09:00 AM – 11:30 PM IST",
            "contract": "MCX Gold (1 kg) / Gold Mini (100g) / Gold Petal (1g)",
            "usdinr_rate": self.mcx_data.get("usdinr_rate", 85.0),
        }
        
        # Calculate MCX Gold equivalent
        current_price = self.technical.get("current_price")
        usdinr = self.mcx_data.get("usdinr_rate", 85.0)
        
        if current_price:
            # MCX Gold per 10 grams = (COMEX per troy oz * USDINR) / 31.1035 * 10
            mcx_per_10g = (current_price * usdinr) / 31.1035 * 10
            mcx_plan["mcx_gold_equivalent"] = round(mcx_per_10g, 0)
            mcx_plan["conversion_note"] = f"COMEX ${current_price:.0f}/oz × ₹{usdinr:.1f}/$ = ₹{mcx_per_10g:,.0f}/10g"
        
        # GOLDBEES stats
        goldbees = self.mcx_data.get("goldbees", None)
        if goldbees is not None and hasattr(goldbees, 'empty') and not goldbees.empty:
            try:
                gb_close = goldbees["Close"].squeeze() if isinstance(goldbees["Close"], __import__('pandas').DataFrame) else goldbees["Close"]
                mcx_plan["goldbees_price"] = round(float(gb_close.iloc[-1]), 2)
                if len(gb_close) >= 2:
                    prev = float(gb_close.iloc[-2])
                    curr = float(gb_close.iloc[-1])
                    mcx_plan["goldbees_change_pct"] = round((curr - prev) / prev * 100, 2)
            except:
                pass
        
        # India market specifics
        signal_val = self.signal.get("signal", 0)
        if signal_val > 0.15:
            mcx_plan["india_bias"] = "Bullish — INR weakness adds to gold upside in ₹ terms"
        elif signal_val < -0.15:
            mcx_plan["india_bias"] = "Bearish — watch for INR strength amplifying gold downside"
        else:
            mcx_plan["india_bias"] = "Neutral — monitor USDINR for direction"
        
        mcx_plan["key_factors"] = [
            "RBI policy stance and USDINR intervention",
            "Physical gold demand (wedding/festival season)",
            "Import duty changes (currently ~15%)",
            "Sovereign Gold Bond issuance calendar",
        ]
        
        return mcx_plan
    
    def _compute_risk_params(self) -> dict:
        """Compute position sizing and risk parameters."""
        current_price = self.technical.get("current_price", 3000)
        
        # ATR-based
        expected_range = self.volatility.get("expected_range", {})
        atr = expected_range.get("atr_14", current_price * 0.015)
        
        risk = {
            "atr_14": atr,
            "atr_pct": round(atr / current_price * 100, 4),
        }
        
        # Stop loss distances
        risk["stop_tight"] = round(atr * 0.5, 2)      # Tight: 0.5 ATR
        risk["stop_normal"] = round(atr * 1.0, 2)      # Normal: 1.0 ATR
        risk["stop_wide"] = round(atr * 1.5, 2)        # Wide: 1.5 ATR
        
        # Target distances
        risk["target_1r"] = round(atr * 1.0, 2)        # 1:1 R:R
        risk["target_2r"] = round(atr * 2.0, 2)        # 1:2 R:R
        risk["target_3r"] = round(atr * 3.0, 2)        # 1:3 R:R
        
        # Position sizing examples (for $100k account, 1% risk per trade)
        for account_size in [10000, 50000, 100000]:
            risk_per_trade = account_size * 0.01  # 1% risk
            contracts_gold_micro = risk_per_trade / (atr * 10)  # Micro gold = $10/point
            contracts_gold_standard = risk_per_trade / (atr * 100)  # Standard = $100/point
            
            risk[f"sizing_{account_size}"] = {
                "account_size": account_size,
                "risk_per_trade_1pct": round(risk_per_trade, 2),
                "micro_gold_contracts": round(contracts_gold_micro, 2),
                "standard_gold_contracts": round(contracts_gold_standard, 2),
            }
        
        # MCX position sizing
        usdinr = self.mcx_data.get("usdinr_rate", 85.0)
        mcx_lot_size = 100  # Gold Mini = 100 grams
        mcx_tick = 1  # ₹1 per gram
        mcx_tick_value = mcx_lot_size * mcx_tick  # ₹100 per tick
        
        risk["mcx_sizing"] = {
            "lot_size_mini": f"{mcx_lot_size}g (Gold Mini)",
            "tick_value": f"₹{mcx_tick_value}",
            "note": "Always check MCX margin requirements before trading"
        }
        
        return risk
    
    def _generate_trade_setups(self) -> list:
        """Generate actionable trade setups."""
        setups = []
        
        signal_val = self.signal.get("signal", 0)
        confidence = self.signal.get("confidence", 0)
        current_price = self.technical.get("current_price", 0)
        pivots = self.technical.get("pivot_points", {}).get("classic", {})
        fib = self.technical.get("fibonacci", {})
        expected = self.volatility.get("expected_range", {})
        atr = expected.get("atr_14", current_price * 0.013)
        
        if not current_price:
            return setups
        
        if signal_val > 0.15 and confidence > 0.3:
            # Bullish setups
            entry_pullback = pivots.get("PP") or current_price - atr * 0.3
            setups.append({
                "type": "LONG",
                "name": "Buy the Dip",
                "entry": round(entry_pullback, 2),
                "stop_loss": round(entry_pullback - atr, 2),
                "target_1": round(entry_pullback + atr * 1.5, 2),
                "target_2": pivots.get("R1") or round(entry_pullback + atr * 2.5, 2),
                "risk_reward": "1:1.5 to 1:2.5",
                "confidence": round(confidence * 100, 1),
                "trigger": "Wait for pullback to pivot point area, enter on bullish candle confirmation"
            })
            
            if pivots.get("R1"):
                setups.append({
                    "type": "LONG",
                    "name": "Breakout Buy",
                    "entry": round(pivots["R1"] + atr * 0.1, 2),
                    "stop_loss": round(pivots["R1"] - atr * 0.5, 2),
                    "target_1": pivots.get("R2") or round(pivots["R1"] + atr * 2, 2),
                    "target_2": round(pivots["R1"] + atr * 3, 2),
                    "risk_reward": "1:2 to 1:3",
                    "confidence": round(confidence * 80, 1),
                    "trigger": "Enter on confirmed breakout above R1 with volume"
                })
        
        elif signal_val < -0.15 and confidence > 0.3:
            # Bearish setups
            entry_rally = pivots.get("PP") or current_price + atr * 0.3
            setups.append({
                "type": "SHORT",
                "name": "Sell the Rally",
                "entry": round(entry_rally, 2),
                "stop_loss": round(entry_rally + atr, 2),
                "target_1": round(entry_rally - atr * 1.5, 2),
                "target_2": pivots.get("S1") or round(entry_rally - atr * 2.5, 2),
                "risk_reward": "1:1.5 to 1:2.5",
                "confidence": round(confidence * 100, 1),
                "trigger": "Wait for rally to pivot area, enter on bearish rejection candle"
            })
        
        else:
            # Neutral — range-bound setups
            if pivots.get("S1") and pivots.get("R1"):
                setups.append({
                    "type": "RANGE",
                    "name": "Range Trade",
                    "buy_zone": pivots["S1"],
                    "sell_zone": pivots["R1"],
                    "stop_loss_long": round(pivots["S1"] - atr * 0.5, 2),
                    "stop_loss_short": round(pivots["R1"] + atr * 0.5, 2),
                    "risk_reward": "1:1 to 1:1.5",
                    "confidence": round(confidence * 70, 1),
                    "trigger": "Trade the range between S1 and R1 with tight stops"
                })
        
        return setups
