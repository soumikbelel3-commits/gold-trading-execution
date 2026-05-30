# Gold Pre-Session Analysis Dashboard

An institutional-grade **Gold Pre-Session Analysis Dashboard** that delivers a one-click market briefing before your trading sessions. Run a single command and get a full multi-factor analysis in ~9 seconds with a live browser dashboard.

## Features

- **Composite Alpha Signal** — Aggregated BUY/SELL/NEUTRAL recommendation with confidence scoring, now blending ML & seasonality
- **Multi-Timeframe Technical Analysis** — 50+ indicators across 1H, 4H, Daily timeframes (RSI, MACD, Bollinger, Ichimoku, Fibonacci, Pivots)
- **Macro Scoring** — DXY, VIX, yields, oil, central bank policy impact on gold
- **Sentiment Engine** — Fear & Greed Index, news sentiment, headline analysis
- **Volatility Surface** — Historical vol, Parkinson vol, percentile rank, expected daily range
- **Cross-Asset Correlations** — 30-day correlations vs gold with regime detection
- **Session Gameplans** — Actionable strategies for Asian/London/NY sessions
- **MCX India** — MCX Gold price in INR, COMEX-MCX conversion, GOLDBEES ETF
- **Trade Setups** — Entry/stop/target levels with R:R ratios
- **Risk Parameters** — ATR-based stops, position sizing for multiple account sizes

### ⚡ Advanced modules (v2.0)

- **Machine Learning Direction Model** — Random Forest + Gradient Boosting + Logistic ensemble, *strictly walk-forward validated* (no look-ahead). Reports next-session up-probability, out-of-sample accuracy vs baseline, ROC-AUC, per-model agreement, and feature importances.
- **Monte Carlo Projection** — 20k simulations of the next session calibrated to recent log-return stats: percentile cones, 1σ band, return distribution histogram, and probability of hitting ±0.5–2% targets.
- **Signal Backtest** — Historical edge of each technical rule (forward N-day return, win-rate, edge vs baseline) plus a composite-score long/flat strategy vs buy-and-hold (Sharpe, max drawdown, equity curve).
- **Market Structure** — S/R **confluence zones** (clusters pivots + fibs + MAs), candlestick pattern recognition, **ADX** trend strength, intraday **VWAP**, and the **Gold/Silver ratio**.
- **Seasonality** — Monthly and day-of-week return patterns over ~15 years, with the current calendar period highlighted.
- **Event Risk & Scenarios** — Proximity to FOMC / NFP / CPI / PCE, a pre-session risk checklist, gold priced in EUR/JPY/GBP, and macro-sensitivity betas (what gold does on a DXY or 10Y-yield move).
- **Dashboard UX** — Refresh / Export (print) / Auto-refresh toolbar and a print-friendly stylesheet.

> The ML and statistical outputs are intentionally honest: on daily gold, direction is close to a coin flip, so accuracy sits near baseline. The edge is in the *probabilities, feature attributions, and regime context* — not false precision. **Research/education only, not financial advice.**

## Project Structure

```
gold-trading-execution/
├── run_session.py              # One-click entry point
├── requirements.txt            # Dependencies
├── engine/                     # Analysis engine (14 modules)
│   ├── __init__.py
│   ├── data_fetcher.py         # Live gold + MCX + cross-asset + long history + FX
│   ├── technical_analyzer.py   # 50+ indicators, Fibonacci, Ichimoku
│   ├── macro_scorer.py         # DXY, yields, VIX, oil scoring
│   ├── sentiment_engine.py     # Reads existing pipeline data
│   ├── volatility_analyzer.py  # Vol surface, percentile, ATR
│   ├── correlation_engine.py   # Cross-asset correlation heatmap
│   ├── ml_engine.py            # Walk-forward ML ensemble (RF + GB + Logistic)
│   ├── montecarlo_engine.py    # Monte Carlo next-session projection
│   ├── backtest_engine.py      # Rule edges + composite-score strategy backtest
│   ├── structure_engine.py     # Confluence zones, patterns, ADX, VWAP, G:S ratio
│   ├── seasonality_engine.py   # Monthly / day-of-week seasonal patterns
│   ├── scenario_engine.py      # Event calendar, macro betas, gold-in-FX, checklist
│   ├── signal_generator.py     # Composite alpha signal (+ ML & seasonality blend)
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
