# Gold Pre-Session Analysis Dashboard

An institutional-grade **Gold Pre-Session Analysis Dashboard** that delivers a one-click market briefing before your trading sessions. Run a single command and get a full multi-factor analysis in ~9 seconds with a live browser dashboard.

## Features

- **Composite Alpha Signal** — Aggregated BUY/SELL/NEUTRAL recommendation with confidence scoring
- **Multi-Timeframe Technical Analysis** — 50+ indicators across 1H, 4H, Daily timeframes (RSI, MACD, Bollinger, Ichimoku, Fibonacci, Pivots)
- **Macro Scoring** — DXY, VIX, yields, oil, central bank policy impact on gold
- **Sentiment Engine** — Fear & Greed Index, news sentiment, headline analysis
- **Volatility Surface** — Historical vol, Parkinson vol, percentile rank, expected daily range
- **Cross-Asset Correlations** — 30-day correlations vs gold with regime detection
- **Session Gameplans** — Actionable strategies for Asian/London/NY sessions
- **MCX India** — MCX Gold price in INR, COMEX-MCX conversion, GOLDBEES ETF
- **Trade Setups** — Entry/stop/target levels with R:R ratios
- **Risk Parameters** — ATR-based stops, position sizing for multiple account sizes

## Project Structure

```
gold-trading-execution/
├── run_session.py              # One-click entry point
├── requirements.txt            # Dependencies
├── engine/                     # Analysis engine (8 modules)
│   ├── __init__.py
│   ├── data_fetcher.py         # Live gold + MCX + cross-asset data
│   ├── technical_analyzer.py   # 50+ indicators, Fibonacci, Ichimoku
│   ├── macro_scorer.py         # DXY, yields, VIX, oil scoring
│   ├── sentiment_engine.py     # Reads existing pipeline data
│   ├── volatility_analyzer.py  # Vol surface, percentile, ATR
│   ├── correlation_engine.py   # Cross-asset correlation heatmap
│   ├── signal_generator.py     # Composite alpha signal
│   └── session_planner.py      # Session gameplan + MCX India
├── dashboard/                  # Browser-based UI
│   ├── index.html              # Layout
│   ├── styles.css              # Dark theme (Bloomberg-inspired)
│   └── app.js                  # Charts & interactive rendering
└── output/                     # Generated analysis output
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the analysis:**
   ```bash
   python run_session.py
   ```

3. The dashboard auto-opens at **http://localhost:8877**

## Data Sources

- **Live data via yfinance** (no API keys needed):
  - Gold Futures (GC=F) — 1H and Daily
  - MCX proxy: GOLDBEES.NS + USD/INR
  - Cross-assets: DXY, US10Y, SPY, TLT, CL, SI, BTC, VIX, GLD

- **Existing Data Collection pipeline** (optional):
  - Sentiment data (Fear & Greed, News, Keywords)
  - Options chain data
  - Composite alpha signals

## Tech Stack

- **Backend:** Python (yfinance, pandas, numpy, scipy, ta)
- **Frontend:** Vanilla HTML/CSS/JS with Lightweight Charts
- **Design:** Bloomberg-inspired dark theme

## License

MIT
