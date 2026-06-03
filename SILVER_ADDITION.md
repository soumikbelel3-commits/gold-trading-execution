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

## Crypto assets (BTC, ETH, SOL, BNB, XRP)

Extended the multi-asset system to **crypto**, a different asset class from
precious metals. Added to the toggle: **Bitcoin, Ethereum, Solana, BNB, XRP**.

### Config
`asset_config.py` now tags every asset with `asset_class` (`metal` / `crypto`).
Crypto entries (built via the `_crypto()` helper) carry: ticker (`BTC-USD`,
`ETH-USD`, `SOL-USD`, `BNB-USD`, `XRP-USD`), a `peer` crypto for correlations,
and spot-unit sizing (point value = $1 per $1 move per coin). `ASSET_ORDER`
drives the pipeline run order and toggle layout.

### Asset-class–aware engines
- **data_fetcher** — crypto cross-asset universe is risk-on oriented:
  `DXY, US10Y, US02Y, SPY, QQQ, Gold, VIX` + BTC/ETH peers. MCX fetch skipped.
- **macro_scorer** — `asset_class="crypto"` **flips the VIX factor** (fear =
  risk-off headwind, the opposite of gold's safe-haven bid) and reframes the
  regime as **financial conditions** ("Easy / Tight"), not a metals-style
  bull/bear call.
- **structure_engine** — gold/silver ratio skipped for crypto.
- **session_planner** — single **24/7 Global Market** session instead of
  Asian/London/NY; MCX panel and MCX sizing skipped; sizing labeled in coin
  units.
- **correlation_engine** — crypto regimes are risk-on framed (Risk-On tracking
  equities/Nasdaq, Crypto-Correlated with BTC, Dollar-Driven, …); all labels
  use the active asset name.

### Dashboard
- 7-asset toggle (Gold · Silver · BTC · ETH · SOL · BNB · XRP).
- For crypto: the **MCX/India card is hidden** and the Session row collapses to
  full width; the macro gauge is relabeled **Risk-Off ↔ Risk-On** with a caveat
  that it's a USD/rates/risk backdrop, not a safe-haven call; chart/title/FX
  labels follow the active coin. The multi-decade chart works (BTC ~11.7y back
  to 2014; ETH/BNB/XRP to 2017; SOL to 2020 — each coin's full history).

### Honesty notes for crypto
- The macro composite still leans on metals-style relationships for some
  factors (e.g. an inverted yield curve scores risk-positive); only the most
  inverted factor (VIX) is flipped. Treat the macro panel as USD/rates/risk
  *context*, per the in-panel caveat.
- Pipeline sentiment parquet is gold/market-sourced and reused as a generic
  market-sentiment proxy.

### Verified (live preview, no console errors)
| Asset | Price | Macro | Correlation regime |
|-------|-------|-------|--------------------|
| Bitcoin | $73,836 | Mildly Easy Conditions | Mixed |
| Ethereum | $2,020 | Mildly Easy Conditions | Crypto-Correlated (with BTC) |
| Solana | $82.67 | Mildly Easy Conditions | Risk-On (tracking Nasdaq) |
| BNB | $721.88 | Mildly Easy Conditions | Mixed |
| XRP | $1.34 | Mildly Easy Conditions | Crypto-Correlated (with BTC) |

MCX card hidden, 24/7 session shown, no gold/silver ratio, macro tilt =
"Risk-Off / Risk-On" for all crypto tabs.

## World indices (panel + index assets)

Two additions: a **World Indices overview panel** and **S&P 500 / Nasdaq 100 as
full toggle assets** (a third asset class, `index`).

### Overview panel
- `data_fetcher.fetch_world_indices()` batch-downloads 14 major global indices
  (S&P 500, Nasdaq, Dow, Russell 2000, FTSE 100, DAX, CAC 40, Euro Stoxx 50,
  Nikkei 225, Hang Seng, Nifty 50, Sensex, KOSPI, ASX 200) → name/symbol/region/
  price/daily %. Attached to every asset's `output["world_indices"]`.
- Frontend: `renderWorldIndices()` draws a responsive tile grid (`#world-indices`),
  color-coded green/red/yellow by daily change. Shown on every asset tab as
  global macro context.

### Index assets (`asset_class: "index"`)
- `asset_config._index()` adds **S&P 500** (`^GSPC`) and **Nasdaq 100** (`^NDX`)
  with index-futures point values (MES $5 / ES $50; MNQ $2 / NQ $20) and a peer
  index for correlations.
- Engines treat `index` as **risk-on, same as crypto**: VIX flipped in macro
  (financial-conditions regime), no MCX, no gold/silver ratio, risk-on
  correlation regimes. New **US Cash Session** model in `session_planner`
  (09:30–16:00 ET) instead of 24/7 or Asian/London/NY.
- The crypto/index branches are unified via `asset_class in ("crypto","index")`
  in macro_scorer & correlation_engine, and `!= "metal"` for MCX/ratio hiding.

### Dashboard
- Toggle now has 9 assets (Gold · Silver · BTC · ETH · SOL · BNB · XRP · S&P 500
  · Nasdaq). Non-metal classes hide MCX + ratio and use the Risk-Off/Risk-On
  macro gauge; index subtitle reads "Equity Index", crypto "24/7 Crypto".

### Verified (live preview, no console errors)
- World Indices panel: 14/14 populated, color-coded (S&P +0.26%, Russell −0.47%,
  Hang Seng +2.52%, Nikkei −0.30% …); visible on every tab.
- S&P 500 tab: $7,600, US Cash Session, MES sizing, "Mildly Easy Conditions"
  macro, BULLISH regime green; MCX hidden, no gold/silver ratio. Nasdaq similar.

## Commodities, Indian stocks & grouped navbar

### Navbar sections
The flat toggle is now four category dropdowns: **Commodity (8) · Crypto (5) ·
Index (2) · Stock (20)**. Long lists (Stock) scroll. Active category shows the
selected asset inline (e.g. "Stock · TCS"). Groups are defined in
`asset_config.ASSET_GROUPS`. File resolution is generic
(`assetFile(key)` → `session_data_<key>.json`, gold → `session_data.json`).

### Commodity class (new) — Crude WTI, Brent, Natural Gas, Copper, Platinum, Palladium
- `asset_config._commodity()`; `asset_class: "commodity"`, USD, futures-point
  sizing (MCL/CL, NG, HG, PL, PA).
- Cyclical/risk-on: VIX flipped in macro, no MCX, no gold/silver ratio, new
  **Global Futures Session** (nearly 24h). Cross-assets: DXY/yields/SPY/VIX +
  Gold/Crude/Copper.

### Stock class (new) — 20 Nifty large-caps (Reliance, TCS, HDFC Bank, …)
- `asset_config._stock()`; `asset_class: "stock"`, **currency `Rs.`**, NSE
  tickers (`*.NS`), sized in shares, peer = Nifty 50.
- **NSE Cash Session** (09:15–15:30 IST). Cross-assets: Nifty 50 / Sensex /
  USD-INR / DXY / VIX / SPY / Gold. Risk-on macro.

### Dynamic currency
- `meta.currency` + `cur()` in `app.js`; all price displays use `cur()` so NSE
  stocks render in **₹** (e.g. ₹2,244). The USD-based "FX priced-in" block and
  its title suffix are hidden for non-USD assets.

### Engine generalization
The risk-on / non-metal branches in macro_scorer, correlation_engine,
structure_engine and session_planner are now keyed on `asset_class != "metal"`
(metals = safe-haven; everything else = risk-on/cyclical), so the four classes
share one code path and new assets are config-only.

### Verified (live preview)
- 35 assets total, all pipelines exit 0. Navbar: Commodity 8 / Crypto 5 /
  Index 2 / Stock 20.
- TCS: ₹2,244, NSE Cash Session, "NSE Equity" subtitle, no MCX/ratio, "Scenarios"
  (FX dropped), NEUTRAL → yellow. Crude: $95.51, Global Futures Session.
- Note: an earlier transient `ASSET_FILES`/`DOMContentLoaded(event)` bug 404'd
  the data; fixed via the generic `assetFile()` + string-guarded `loadData`.

## Finviz-style World Indices + Day/Night theme

### World Indices sparklines (Finviz-style)
- `data_fetcher.fetch_world_indices()` now also returns an intraday `spark`
  series per index (batched `period=1d, interval=5m`, downsampled to <=48 pts;
  falls back to a few daily closes if intraday is unavailable).
- Frontend `renderWorldIndices()` draws an inline-SVG sparkline per tile
  (`sparkSvg()`), with the line/area/left-border coloured **green when up, red
  when down** (CSS via `.index-cell.up/.down`), plus last price and daily %.
  Tiles match Finviz's world-indices look.
- The new `world_indices` (with `spark`) was patched into all 70 existing JSON
  files (dashboard + output) without a full pipeline rerun.

### Day / Night toggle
- A theme button in the toolbar flips between dark (default) and a new **light
  theme** (`body.theme-light` CSS-variable overrides). Choice persists in
  `localStorage` (`dashTheme`) and is applied on load before first render.
- Lightweight Charts are theme-aware via `themeColors()` (background / text /
  grid / border); toggling re-renders the price chart + backtest equity curve
  so their canvases match the theme. Semantic green/red/yellow are tuned darker
  in light mode for contrast.

## Caveats / future tweaks
- Pipeline **sentiment** parquet (Fear & Greed / news) is market-wide/gold-
  sourced; it's reused for silver as a market-sentiment proxy and labeled
  generically ("Market Headlines").
- `correlation_engine` still prints one hardcoded regime string mentioning
  "Gold" in the console summary (cosmetic; dashboard badge is fine).
- MCX silver tick value is approximate — verify against current MCX contract
  specs before relying on position sizing.
