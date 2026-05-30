# CLAUDE.md

Gold pre-session trading-analysis dashboard. A Python engine fetches live market data, runs multi-factor analysis, writes one JSON file, and serves a vanilla-JS browser dashboard. **Research/education only — not financial advice.**

## Run

```bash
pip install -r requirements.txt
python run_session.py          # fetches data (~30s), writes JSON, serves dashboard at http://localhost:8877
```

Single entry point: `run_session.py`. `run_analysis()` runs the pipeline and returns a dict; `save_output()` writes it to `output/session_data.json` **and** `dashboard/session_data.json` (the dashboard fetches the copy in its own folder).

## Architecture

Pipeline (in `run_session.run_analysis`): fetch data → run each engine → `signal_generator` blends everything → `session_planner` + `scenario_engine` → assemble `output` dict → save → serve.

`engine/` modules (each is a class with an `analyze()`/`score_all()`/`generate()` method returning a plain dict):
- `data_fetcher.py` — yfinance live data: gold 1H/4H/daily (`GC=F`), long history (`period=max`, capped 3800 rows) for ML/seasonality/backtest, cross-assets (DXY, ^TNX, SPY, TLT, oil, silver, BTC, VIX, GLD), FX rates, MCX/GOLDBEES + USDINR. Also reads optional parquet files from a sibling `../Data collection/` pipeline (sentiment/options/signals) — gracefully absent.
- `technical_analyzer.py` — 50+ indicators across timeframes, Fibonacci, pivots, Ichimoku, candle data for charts.
- `macro_scorer.py` — scores DXY/VIX/yields/curve/oil/CB each −3..+3.
- `sentiment_engine.py` — aggregates pipeline sentiment parquet (Fear&Greed, news).
- `volatility_analyzer.py` — HV windows, Parkinson, percentile, ATR range, regime.
- `correlation_engine.py` — 30/90d cross-asset corr, regime, divergences.
- `ml_engine.py` — RF+GB+Logistic ensemble, **walk-forward** (TimeSeriesSplit, no look-ahead). Needs scikit-learn. Honest: daily-direction accuracy ≈ baseline.
- `montecarlo_engine.py` — GBM sim of next session: percentiles, histogram, target probabilities.
- `backtest_engine.py` — per-rule forward-return edge + composite-score long/flat strategy vs buy-hold.
- `structure_engine.py` — S/R confluence zones (clusters pivots+fibs+MAs), candlestick patterns, ADX, VWAP, gold/silver ratio, swing structure.
- `seasonality_engine.py` — monthly/quarterly/day-of-week patterns from long history.
- `scenario_engine.py` — event calendar (FOMC/NFP/CPI/PCE), macro betas/scenarios, gold in EUR/JPY/GBP, risk checklist.
- `signal_generator.py` — weighted composite of technical/macro/sentiment/volatility/correlation/ml/seasonality → signal, confidence, action, regime.
- `session_planner.py` — Asian/London/NY gameplans, MCX India, risk params, trade setups.

`dashboard/` — `index.html` (layout, loads `?v=N` cache-busted assets), `styles.css` (Linear-inspired dark theme; CSS vars at top; `.grid` uses `align-items: stretch` + `.card` flex-column for equal-height aligned rows), `app.js` (one `render*()` per section, all wired in `renderAll()`; uses Lightweight Charts).

## Conventions & gotchas

- **Adding an engine:** create `engine/<x>.py` with a class; instantiate + call in `run_analysis`; add its dict to `output`; add a `render<X>()` in `app.js` + section in `index.html` + styles; wire into `renderAll()`. Keep JSON serializable (numpy handled by `save_output`'s custom serializer).
- **yfinance** returns MultiIndex columns — every fetch flattens with `.get_level_values(0)`. Data is live/network-dependent; handle empty DataFrames.
- **Windows:** `run_session.py` forces UTF-8 stdout. Use ASCII in console prints (`[OK]`, `WARNING:`) — no emoji in Python prints.
- **Frontend cache:** assets are `styles.css?v=N` / `app.js?v=N`. `run_session.py`'s server sends no-cache headers, but plain `python -m http.server` does NOT — **bump `?v=N` in `index.html` when editing CSS/JS** so changes load.
- **Preview during dev:** `.claude/launch.json` defines a `dashboard` server on port 8898 (serves `dashboard/`). After editing CSS/JS, bump `?v=N` then reload.
- `scenario_engine.FOMC_2026` dates are approximate — verify against the official Fed calendar.
- Don't commit/push unless asked.

## Memory
Persistent notes live in `C:\Users\Rishi\.claude\projects\...\memory\` (see `dashboard-v2-advanced-modules.md`).
