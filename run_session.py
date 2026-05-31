"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║    ██████╗  ██████╗ ██╗     ██████╗                                     ║
║   ██╔════╝ ██╔═══██╗██║     ██╔══██╗                                    ║
║   ██║  ███╗██║   ██║██║     ██║  ██║                                    ║
║   ██║   ██║██║   ██║██║     ██║  ██║                                    ║
║   ╚██████╔╝╚██████╔╝███████╗██████╔╝                                    ║
║    ╚═════╝  ╚═════╝ ╚══════╝╚═════╝                                     ║
║                                                                          ║
║   PRE-SESSION ANALYSIS DASHBOARD — Gold (XAU/USD) & MCX Gold            ║
║   Institutional-Grade Trading Preparation System                         ║
║                                                                          ║
║   Usage:  python run_session.py                                          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import webbrowser
import http.server
import socketserver
import threading
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
os.environ['PYTHONUTF8'] = '1'
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

import warnings
warnings.filterwarnings("ignore")

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.data_fetcher import GoldDataFetcher
from engine.technical_analyzer import GoldTechnicalAnalyzer
from engine.macro_scorer import GoldMacroScorer
from engine.sentiment_engine import GoldSentimentEngine
from engine.volatility_analyzer import GoldVolatilityAnalyzer
from engine.correlation_engine import GoldCorrelationEngine
from engine.signal_generator import GoldSignalGenerator
from engine.session_planner import GoldSessionPlanner
from engine.seasonality_engine import GoldSeasonalityEngine
from engine.montecarlo_engine import GoldMonteCarloEngine
from engine.backtest_engine import GoldBacktestEngine
from engine.structure_engine import GoldStructureEngine
from engine.scenario_engine import GoldScenarioEngine
from engine.ml_engine import GoldMLEngine
from engine.asset_config import ASSETS, DEFAULT_ASSET


# ═══════════════════════════════════════════════════════════
# OUTPUT CONFIG
# ═══════════════════════════════════════════════════════════
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
PORT = 8877


def run_analysis(asset_key: str = DEFAULT_ASSET) -> dict:
    """
    Execute the full pre-session analysis pipeline for the given metal
    ("gold" or "silver"). Returns the complete analysis dictionary.
    """
    cfg = ASSETS.get(asset_key, ASSETS[DEFAULT_ASSET])
    metal = cfg["name"]

    print()
    print("=" * 65)
    print(f"  {metal.upper()} PRE-SESSION ANALYSIS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Local Time)")
    print("=" * 65)
    print()

    start_time = time.time()

    # ── 1. Data Acquisition ──
    fetcher = GoldDataFetcher(asset_key)
    data = fetcher.fetch_all()
    
    # ── 2. Technical Analysis ──
    print("[TECH] Running technical analysis...")
    tech_analyzer = GoldTechnicalAnalyzer(data["gold"])
    technical = tech_analyzer.analyze_all()
    print(f"  [OK] Price: ${technical['current_price']}" if technical['current_price'] else "  [!] Price unavailable")

    # Long-range chart history: resample the full daily history into weekly and
    # monthly candles for the dashboard's "Max" / "30Y" chart tabs. Kept separate
    # from the 1-year `daily` series that the indicators/Fibonacci rely on.
    import pandas as _pd
    chart_hist = data.get("gold_chart", _pd.DataFrame())
    if chart_hist is not None and not chart_hist.empty and "Close" in chart_hist.columns:
        agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
        try:
            weekly = chart_hist.resample("W").agg(agg).dropna()
            monthly = chart_hist.resample("MS").agg(agg).dropna()
            technical.setdefault("candlestick_data", {})
            technical["candlestick_data"]["max"] = tech_analyzer._format_candles(weekly, len(weekly))
            technical["candlestick_data"]["monthly"] = tech_analyzer._format_candles(monthly, len(monthly))
            yrs = round((chart_hist.index[-1] - chart_hist.index[0]).days / 365.25, 1)
            print(f"  [OK] Long-range chart: {yrs}y ({len(weekly)} weekly / {len(monthly)} monthly candles)")
        except Exception as e:
            print(f"  [!] Long-range chart build failed: {e}")
    
    # ── 3. Macro Scoring ──
    print("[MACRO] Scoring macro environment...")
    macro_scorer = GoldMacroScorer(
        dxy=data.get("dxy"),
        vix=data.get("vix"),
        yields=data.get("yields", {}),
        cross_assets=data.get("cross_assets", {}),
        metal=metal,
    )
    macro = macro_scorer.score_all()
    print(f"  [OK] Macro regime: {macro['regime']}")
    
    # ── 4. Sentiment Analysis ──
    print("[SENT] Analyzing sentiment...")
    sentiment_engine = GoldSentimentEngine(data.get("sentiment", {}))
    sentiment = sentiment_engine.analyze()
    print(f"  [OK] Sentiment: {sentiment['composite_label']}")
    
    # ── 5. Volatility Analysis ──
    print("[VOL] Analyzing volatility...")
    vol_analyzer = GoldVolatilityAnalyzer(data["gold"], data.get("vix"))
    volatility = vol_analyzer.analyze()
    print(f"  [OK] Vol regime: {volatility['regime']}")
    
    # ── 6. Cross-Asset Correlations ──
    print("[CORR] Computing cross-asset correlations...")
    corr_engine = GoldCorrelationEngine(
        data["gold"].get("daily", __import__('pandas').DataFrame()),
        data.get("cross_assets", {})
    )
    correlation = corr_engine.analyze()
    print(f"  [OK] Correlation regime: {correlation['regime']}")

    daily_df = data["gold"].get("daily", __import__('pandas').DataFrame())
    h1_df = data["gold"].get("1h", __import__('pandas').DataFrame())
    gold_long = data.get("gold_long", __import__('pandas').DataFrame())

    # ── 6b. Market Structure ──
    print("[STRUCT] Analyzing market structure (confluence, patterns, ADX, VWAP)...")
    structure = GoldStructureEngine(
        daily_df, h1_df, technical, data.get("cross_assets", {}), asset_cfg=cfg
    ).analyze()
    print(f"  [OK] Confluence zones: {len(structure.get('confluence_zones', []))}, "
          f"ADX: {structure.get('adx', {}).get('strength', 'N/A')}")

    # ── 6c. Seasonality ──
    print("[SEASON] Computing seasonal patterns...")
    seasonality = GoldSeasonalityEngine(gold_long).analyze()
    print(f"  [OK] {seasonality.get('summary', 'N/A')[:70]}")

    # ── 6d. Monte Carlo ──
    print("[MC] Running Monte Carlo next-session projection...")
    montecarlo = GoldMonteCarloEngine(daily_df).analyze()
    if montecarlo.get("available"):
        print(f"  [OK] P(up)={montecarlo['prob_up']}%  band ${montecarlo['expected_band']['low']}-${montecarlo['expected_band']['high']}")

    # ── 6e. Backtest ──
    print("[BT] Backtesting technical rules & composite strategy...")
    backtest = GoldBacktestEngine(gold_long).analyze()
    if backtest.get("available"):
        print(f"  [OK] {len(backtest.get('rules', []))} rules backtested over {backtest.get('baseline', {}).get('samples', 0)} samples")

    # ── 6f. Machine Learning ──
    print("[ML] Training ML ensemble (RF + GB + Logistic, walk-forward)...")
    ml = GoldMLEngine(gold_long).analyze()
    if ml.get("available"):
        print(f"  [OK] Ensemble OOS acc {ml['ensemble']['accuracy']}% (baseline {ml['ensemble']['baseline_accuracy']}%) | "
              f"Next: {ml['prediction']['direction']} {ml['prediction']['prob_up']}%")
    else:
        print(f"  [!] ML unavailable: {ml.get('reason', 'unknown')}")

    # ── 7. Composite Signal ──
    print("[SIGNAL] Generating composite signal...")
    signal_gen = GoldSignalGenerator()
    composite_signal = signal_gen.generate(
        technical=technical,
        macro=macro,
        sentiment=sentiment,
        volatility=volatility,
        correlation=correlation,
        pipeline_signals=data.get("pipeline_signals"),
        ml=ml,
        seasonality=seasonality,
    )
    print(f"  [OK] Signal: {composite_signal['signal']:+.4f} ({composite_signal['action']})")
    print(f"  [OK] Confidence: {composite_signal['confidence']:.1%}")
    
    # ── 8. Session Gameplan ──
    print("[SESSION] Building session gameplan...")
    planner = GoldSessionPlanner(
        technical=technical,
        macro=macro,
        volatility=volatility,
        composite_signal=composite_signal,
        mcx_data=data.get("mcx", {}),
        asset_cfg=cfg,
    )
    session_plan = planner.plan()
    print(f"  [OK] Active session: {session_plan['active_session']}")

    # ── 9. Scenario & Event Risk ──
    print("[SCENARIO] Building event calendar, macro betas, FX, checklist...")
    scenario = GoldScenarioEngine(
        technical=technical,
        gold_daily=daily_df,
        cross_assets=data.get("cross_assets", {}),
        fx=data.get("fx", {}),
        macro=macro,
        volatility=volatility,
    ).analyze()
    next_evt = scenario.get("events", [{}])[0] if scenario.get("events") else {}
    print(f"  [OK] Next event: {next_evt.get('event', 'N/A')} in {next_evt.get('days_until', '?')}d")

    # ── Assemble Output ──
    elapsed = time.time() - start_time

    output = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "version": "2.1.0",
            "asset": cfg["key"],
            "asset_name": cfg["name"],
            "asset_symbol": cfg["symbol"],
            "asset_logo": cfg["logo"],
        },
        "technical": technical,
        "macro": macro,
        "sentiment": sentiment,
        "volatility": volatility,
        "correlation": correlation,
        "structure": structure,
        "seasonality": seasonality,
        "montecarlo": montecarlo,
        "backtest": backtest,
        "ml": ml,
        "scenario": scenario,
        "composite_signal": composite_signal,
        "session_plan": session_plan,
    }
    
    # Print summary
    _print_summary(output)
    
    return output


def _print_summary(output: dict):
    """Print a concise console summary."""
    print()
    print("=" * 65)
    print("  ANALYSIS SUMMARY")
    print("=" * 65)
    
    tech = output["technical"]
    sig = output["composite_signal"]
    macro = output["macro"]
    vol = output["volatility"]
    session = output["session_plan"]
    
    price = tech.get("current_price", "N/A")
    change = tech.get("daily_change", 0)
    change_pct = tech.get("daily_change_pct", 0)
    meta = output["meta"]
    asset_label = f"{meta.get('asset_name', 'Gold')} ({meta.get('asset_symbol', 'XAU/USD')})"

    print(f"""
  {asset_label}:  ${price}  ({change:+.2f} / {change_pct:+.3f}%)
  -------------------------------------------------
  Technical Bias:   {tech.get('overall_bias', 'N/A')} (Score: {tech.get('overall_score', 0)})
  Macro Regime:     {macro.get('regime', 'N/A')} ({macro.get('composite_score', 0):+.1f})
  Sentiment:        {output['sentiment'].get('composite_label', 'N/A')}
  Volatility:       {vol.get('regime', 'N/A')}
  Correlation:      {output['correlation'].get('regime', 'N/A')}
  -------------------------------------------------
  COMPOSITE SIGNAL: {sig['signal']:+.4f}
  ACTION:           {sig['action']}
  CONFIDENCE:       {sig['confidence']:.1%}
  REGIME:           {sig['regime']}
  -------------------------------------------------
  Active Session:   {session.get('active_session', 'N/A')}
  Generated:        {output['meta']['generated_at'][:19]}
  Analysis Time:    {output['meta']['elapsed_seconds']}s
""")


def save_output(output: dict, asset_key: str = DEFAULT_ASSET):
    """Save analysis output as JSON for the dashboard."""
    cfg = ASSETS.get(asset_key, ASSETS[DEFAULT_ASSET])
    out_name = cfg["output_file"]
    filepath = OUTPUT_DIR / out_name

    # Custom serializer for numpy/pandas types
    def default_serializer(obj):
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, 'item'):
            return obj.item()
        return str(obj)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=default_serializer, ensure_ascii=False)
    
    # Also copy to dashboard dir for serving
    dash_copy = DASHBOARD_DIR / out_name
    with open(dash_copy, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=default_serializer, ensure_ascii=False)
    
    print(f"  Saved: {filepath}")
    print(f"  Dashboard copy: {dash_copy}")


def serve_dashboard():
    """Start a local HTTP server and open the dashboard."""
    os.chdir(str(DASHBOARD_DIR))
    
    class NoCacheRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()
            
        def log_message(self, format, *args):
            pass  # Suppress logs
            
    handler = NoCacheRequestHandler
    
    try:
        # Use allow_reuse_address to avoid port conflict errors if restarted quickly
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"\n  Dashboard: {url}")
            print(f"  Press Ctrl+C to stop\n")
            
            # Open browser
            webbrowser.open(url)
            
            httpd.serve_forever()
    except OSError:
        # Port in use — try opening in browser anyway
        url = f"http://localhost:{PORT}"
        print(f"\n  Port {PORT} may already be in use.")
        print(f"  Trying to open: {url}")
        webbrowser.open(url)
        
        # Try an alternative port
        try:
            alt_port = PORT + 1
            with socketserver.TCPServer(("", alt_port), handler) as httpd:
                url = f"http://localhost:{alt_port}"
                print(f"  Dashboard on alternative port: {url}")
                webbrowser.open(url)
                httpd.serve_forever()
        except:
            print("  Could not start server. Open dashboard/index.html manually.")
            input("  Press Enter to exit...")


def main():
    """Main entry point."""
    try:
        # Run the full pipeline for each metal and save its own JSON.
        # The dashboard's Gold/Silver toggle swaps between these files.
        for asset_key in ("gold", "silver"):
            output = run_analysis(asset_key)
            print(f"[SAVE] Saving {ASSETS[asset_key]['name']} results...")
            save_output(output, asset_key)

        # Serve dashboard
        print("\n[WEB] Starting dashboard server...")
        serve_dashboard()
        
    except KeyboardInterrupt:
        print("\n\n  Shutting down...")
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\n  Press Enter to exit...")


if __name__ == "__main__":
    main()
