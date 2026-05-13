"""Quick test runner for the analysis pipeline — Windows safe."""
import sys, os, io

# Force UTF-8 for Windows console
os.environ['PYTHONUTF8'] = '1'
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

sys.path.insert(0, r'g:\Antigravity\Quant research\Data collection\.venv\Lib\site-packages')
sys.path.insert(0, r'g:\Antigravity\Quant research\gold trading execution ( claude)')

import warnings
warnings.filterwarnings('ignore')

from engine.data_fetcher import GoldDataFetcher
from engine.technical_analyzer import GoldTechnicalAnalyzer
from engine.macro_scorer import GoldMacroScorer
from engine.sentiment_engine import GoldSentimentEngine
from engine.volatility_analyzer import GoldVolatilityAnalyzer
from engine.correlation_engine import GoldCorrelationEngine
from engine.signal_generator import GoldSignalGenerator
from engine.session_planner import GoldSessionPlanner
import json, time
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

print('=' * 65)
print('  GOLD PRE-SESSION ANALYSIS')
print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (Local Time)')
print('=' * 65)
print()

start = time.time()

# 1. Fetch data
fetcher = GoldDataFetcher()
data = fetcher.fetch_all()

# 2. Technical
print('[TECH] Running technical analysis...')
tech = GoldTechnicalAnalyzer(data['gold'])
technical = tech.analyze_all()
price_str = f'${technical["current_price"]}' if technical['current_price'] else 'unavailable'
print(f'  Price: {price_str}')

# 3. Macro
print('[MACRO] Scoring macro...')
macro_scorer = GoldMacroScorer(
    dxy=data.get('dxy'), vix=data.get('vix'),
    yields=data.get('yields', {}), cross_assets=data.get('cross_assets', {})
)
macro = macro_scorer.score_all()
print(f'  Macro: {macro["regime"]}')

# 4. Sentiment
print('[SENT] Analyzing sentiment...')
sent_engine = GoldSentimentEngine(data.get('sentiment', {}))
sentiment = sent_engine.analyze()
print(f'  Sentiment: {sentiment["composite_label"]}')

# 5. Volatility
print('[VOL] Analyzing volatility...')
vol = GoldVolatilityAnalyzer(data['gold'], data.get('vix'))
volatility = vol.analyze()
print(f'  Vol: {volatility["regime"]}')

# 6. Correlation
print('[CORR] Computing correlations...')
corr = GoldCorrelationEngine(data['gold'].get('daily', pd.DataFrame()), data.get('cross_assets', {}))
correlation = corr.analyze()
print(f'  Corr: {correlation["regime"]}')

# 7. Signal
print('[SIGNAL] Generating signal...')
sig_gen = GoldSignalGenerator()
signal = sig_gen.generate(technical, macro, sentiment, volatility, correlation, data.get('pipeline_signals'))
print(f'  Signal: {signal["signal"]:+.4f} ({signal["action"]})')
print(f'  Confidence: {signal["confidence"]:.1%}')

# 8. Session plan
print('[SESSION] Building session plan...')
planner = GoldSessionPlanner(technical, macro, volatility, signal, data.get('mcx', {}))
session = planner.plan()
print(f'  Active: {session["active_session"]}')

elapsed = time.time() - start

# Assemble
output = {
    'meta': {'generated_at': datetime.now().isoformat(), 'elapsed_seconds': round(elapsed, 2), 'version': '1.0.0'},
    'technical': technical,
    'macro': macro,
    'sentiment': sentiment,
    'volatility': volatility,
    'correlation': correlation,
    'composite_signal': signal,
    'session_plan': session,
}

def ser(obj):
    if isinstance(obj, (np.integer,)): return int(obj)
    elif isinstance(obj, (np.floating,)): return float(obj)
    elif isinstance(obj, (np.ndarray,)): return obj.tolist()
    elif isinstance(obj, (np.bool_,)): return bool(obj)
    elif hasattr(obj, 'isoformat'): return obj.isoformat()
    elif hasattr(obj, 'item'): return obj.item()
    return str(obj)

# Save
outdir = Path(r'g:\Antigravity\Quant research\gold trading execution ( claude)\output')
dashdir = Path(r'g:\Antigravity\Quant research\gold trading execution ( claude)\dashboard')
outdir.mkdir(exist_ok=True)

with open(outdir / 'session_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, default=ser, ensure_ascii=False)
with open(dashdir / 'session_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, default=ser, ensure_ascii=False)

print()
print('=' * 65)
print('  ANALYSIS COMPLETE')
print('=' * 65)
cp = technical.get('current_price', 'N/A')
print(f'  Gold (XAU/USD):  ${cp}')
print(f'  Technical:       {technical.get("overall_bias", "N/A")} (Score: {technical.get("overall_score", 0)})')
print(f'  Macro Regime:    {macro.get("regime", "N/A")} ({macro.get("composite_score", 0):+.1f})')
print(f'  Sentiment:       {sentiment.get("composite_label", "N/A")}')
print(f'  Volatility:      {volatility.get("regime", "N/A")}')
print(f'  Correlation:     {correlation.get("regime", "N/A")}')
print(f'  ---')
print(f'  SIGNAL:          {signal["signal"]:+.4f} | {signal["action"]}')
print(f'  CONFIDENCE:      {signal["confidence"]:.1%}')
print(f'  REGIME:          {signal["regime"]}')
print(f'  ---')
print(f'  Analysis Time:   {elapsed:.1f}s')
print(f'  Output:          output/session_data.json')
print(f'  Dashboard:       dashboard/index.html')
print('=' * 65)
