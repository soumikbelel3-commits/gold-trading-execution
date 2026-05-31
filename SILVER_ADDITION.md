# Silver Pre-Session Analysis — Implementation Notes

Added a **Silver (XAG/USD)** analysis alongside the existing Gold dashboard.
Delivered as **one unified dashboard with a Gold/Silver toggle** in the header.
The backend runs the *same* pipeline for both metals and writes two JSON files;
the frontend swaps which file it loads and re-labels the asset-specific text.

> Research/education only — not financial advice.

---

## How it works now

```bash
python run_session.py
```

`run_session.py` now runs the full pipeline **twice** — once for gold, once for
silver — and writes:

| Asset  | Output (also copied to `dashboard/`) |
|--------|--------------------------------------|
| Gold   | `output/session_data.json`           |
| Silver | `output/session_data_silver.json`    |

Open the dashboard and use the **`Au · Gold` / `Ag · Silver`** toggle in the
top-left header to switch between them. No page reload needed — the toggle
fetches the other JSON and re-renders every panel.

---

## Key design decision

Almost every `engine/` module is **asset-agnostic** — it takes plain
DataFrames/dicts, not a hardcoded ticker. So the analytical engines (technical,
volatility, correlation, ML, Monte Carlo, backtest, seasonality, sentiment,
signal generator, scenario) are **reused unchanged** on silver data. Only the
data source, a few labels, and the India/MCX + futures contract specs are truly
metal-specific. All of those now live in one config file.

---

## Files changed

### New
- **`engine/asset_config.py`** — `ASSETS` map for `gold` and `silver`. Holds:
  ticker (`GC=F` / `SI=F`), display name/symbol/logo, the *counter-metal* used
  for the gold/silver ratio, the ETF (`GLD` / `SLV`), MCX proxy + contract specs
  (`GOLDBEES.NS` per-10g vs `SILVERBEES.NS` per-kg), and COMEX futures point
  values used for position sizing.

### Backend (parameterized, gold behavior unchanged by default)
- **`engine/data_fetcher.py`** — `GoldDataFetcher(asset_key="gold")`. Swaps the
  price ticker and MCX proxy from the config, and puts the *other* metal into
  the cross-asset universe so the gold/silver ratio + correlations work for
  whichever metal is active.
- **`engine/macro_scorer.py`** — added `metal="Gold"` param. The macro
  relationships (inverse to DXY/real yields, safe-haven + inflation-hedge
  demand) hold for silver too, so regime/detail strings are relabeled for the
  active metal.
- **`engine/structure_engine.py`** — the Gold/Silver ratio is now asset-aware:
  the traded metal's price comes from `current_price`, the counter-metal from
  cross-assets. Always reported as the conventional Gold/Silver ratio.
- **`engine/session_planner.py`** — MCX equivalent (₹/10g for gold vs ₹/kg for
  silver), contract description, lot/tick, and futures position sizing all read
  from the asset config.
- **`run_session.py`** — `run_analysis(asset_key)`; `main()` loops `("gold",
  "silver")`, saving each to its own JSON. Output `meta` now carries
  `asset` / `asset_name` / `asset_symbol` / `asset_logo`. Version bumped to 2.1.0.

### Frontend (one dashboard)
- **`dashboard/index.html`** — added the `#asset-toggle`; gave the logo, title,
  subtitle, chart/MCX/scenarios headers and footer stable `id`s so labels can be
  set dynamically. Cache-bust bumped (`styles.css?v=5`, `app.js?v=3`).
- **`dashboard/app.js`** — `currentAsset` state + `ASSET_FILES` map;
  `loadData(asset)` fetches the right JSON; `applyAssetLabels()` rewrites all
  metal-worded labels from `DATA.meta`; `setupAssetToggle()` wires the buttons.
  Inline "Gold" strings (macro tilt, MCX, risk sizing, FX, sentiment) now use
  the active metal name.
- **`dashboard/styles.css`** — `.asset-toggle` / `.asset-btn` segmented-control
  styling (uses existing CSS vars).

---

## JSON-key compatibility note

To reuse the existing renderers untouched, **JSON key names were kept identical
across both assets** (e.g. `mcx_gold_equivalent`, `micro_gold_contracts`,
`gold_in_fx`, `gold_silver_ratio`). For silver these keys simply hold the
silver-appropriate numbers (e.g. `mcx_gold_equivalent` = MCX Silver ₹/kg). A few
extra fields were added for correct display: `mcx_name`, `mcx_unit_label`,
`proxy_label`, `micro_label`, and `gold_price` inside the ratio object.

---

## Verified

Both pipelines run clean (exit 0). Live preview check:

| | Gold | Silver |
|---|------|--------|
| Price | $4593.00 | $75.88 |
| Macro regime | Mildly Bearish Gold | Mildly Bearish Silver |
| MCX | ₹140,270 / 10g (GOLDBEES) | ₹231,722 / kg (SILVERBEES) |
| Sizing | Micro Gold | Micro Silver |
| Gold/Silver ratio | 60.7 | 60.1 (consistent) |

Toggle switches price, logo (Au↔Ag), all titles, MCX/FX/macro labels, and the
chart — no console errors.

---

## Long-range price chart (added after initial silver build)

The price chart originally showed only ~120 daily candles (~6 months). It now
offers four ranges via the chart tabs: **1H · 1Y · Max (Wk) · Max (Mo)**.

- `data_fetcher.fetch_chart_history()` pulls the **full uncapped** daily history
  (`period=max`), kept separate from the ML-capped `gold_long`.
- `run_session.py` resamples it to **weekly** and **monthly** OHLC and stores
  them under `technical.candlestick_data["max"]` / `["monthly"]`.
- The 1-year `daily` series (and its indicators/Fibonacci) is unchanged; the
  pivot/Fib/SMA overlays are suppressed on the multi-decade views.

**Data-source limit:** yfinance's `GC=F` / `SI=F` futures history begins in
**Sept 2000 (~25.7 years)** — that's the maximum these free tickers provide, so
a true 30-year daily chart isn't possible from this source. A genuine 30y+
series would require a spot/LBMA history feed (e.g. a paid API or a CSV import)
wired in as an alternate `fetch_chart_history` source.

## Caveats / future tweaks
- Pipeline **sentiment** parquet (Fear & Greed / news) is market-wide/gold-
  sourced; it's reused for silver as a market-sentiment proxy and labeled
  generically ("Market Headlines").
- `correlation_engine` still prints one hardcoded regime string mentioning
  "Gold" in the console summary (cosmetic; dashboard badge is fine).
- MCX silver tick value is approximate — verify against current MCX contract
  specs before relying on position sizing.
