/**
 * ═══════════════════════════════════════════════════════════════
 *  Gold Pre-Session Dashboard — Interactive Frontend
 *  Renders all analysis data from session_data.json
 * ═══════════════════════════════════════════════════════════════
 */

let DATA = null;
let chart = null;
let candleSeries = null;

// ── Asset selection ──
// Gold uses the legacy filename; every other asset is session_data_<key>.json.
function assetFile(asset) {
    return asset === 'gold' ? 'session_data.json' : 'session_data_' + asset + '.json';
}
let currentAsset = 'gold';

// Name of the active asset, used in dynamically-built labels.
function metal() { return (DATA && DATA.meta && DATA.meta.asset_name) || 'Gold'; }
// Asset class: "metal", "crypto", or "index".
function assetClass() { return (DATA && DATA.meta && DATA.meta.asset_class) || 'metal'; }
function isMetal() { return assetClass() === 'metal'; }
function isCrypto() { return assetClass() === 'crypto'; }
// Price currency symbol for the active asset ($ default, Rs. for NSE stocks).
function cur() { return (DATA && DATA.meta && DATA.meta.currency) || '$'; }

// ── Theme (day / night) ──
let currentTf = 'daily';   // active price-chart timeframe (for re-render on theme switch)
function themeColors() {
    const light = document.body.classList.contains('theme-light');
    return light
        ? { bg: '#FFFFFF', text: '#54585F', grid: 'rgba(0,0,0,0.06)', border: 'rgba(0,0,0,0.12)' }
        : { bg: '#0C0C0E', text: '#8B8B8E', grid: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.06)' };
}
function applyTheme(theme) {
    document.body.classList.toggle('theme-light', theme === 'light');
    const btn = document.getElementById('theme-btn');
    if (btn) btn.textContent = theme === 'light' ? '☀ Day' : '🌙 Dark';
}
function initTheme() {
    let t = 'dark';
    try { t = localStorage.getItem('dashTheme') || 'dark'; } catch (e) {}
    applyTheme(t);
}
function toggleTheme() {
    const next = document.body.classList.contains('theme-light') ? 'dark' : 'light';
    try { localStorage.setItem('dashTheme', next); } catch (e) {}
    applyTheme(next);
    // Re-render the canvas charts so their backgrounds match the theme.
    if (DATA) { renderChart(currentTf); renderBacktest(); }
}

// ── Load Data ──
async function loadData(asset) {
    if (typeof asset === 'string') currentAsset = asset;
    const file = assetFile(currentAsset);
    try {
        const response = await fetch(file + '?t=' + Date.now());
        if (!response.ok) throw new Error('HTTP ' + response.status);
        DATA = await response.json();
        if (DATA.meta && DATA.meta.asset) currentAsset = DATA.meta.asset;
        document.getElementById('loading').style.display = 'none';
        document.getElementById('dashboard').style.display = 'block';
        renderAll();
    } catch (error) {
        document.querySelector('.loading-text').textContent =
            'Error loading ' + currentAsset + ' data. Make sure run_session.py has been executed.';
        console.error('Failed to load session data:', error);
    }
}

// ── Render All Sections ──
function renderAll() {
    applyAssetLabels();
    renderHeader();
    renderSignalBar();
    renderChart('daily');
    renderKeyLevels();
    renderTechnicalScorecard();
    renderMacro();
    renderSentiment();
    renderCorrelation();
    renderVolatility();
    renderIchimoku();
    renderPivotPoints('classic');
    renderSessionPlan();
    renderMCX();
    renderTradeSetups();
    renderRiskParams();
    renderML();
    renderMonteCarlo();
    renderWorldIndices();
    renderConfluence();
    renderStructure();
    renderSeasonality();
    renderBacktest();
    renderEvents();
    renderScenarios();
    setupChartTabs();
    setupPivotTabs();
    setupToolbar();
    setupAssetToggle();
}

// ═══════════════════════════════════════
// ASSET-AWARE LABELS + TOGGLE
// ═══════════════════════════════════════
function applyAssetLabels() {
    const m = metal();
    const meta = (DATA && DATA.meta) || {};
    const sym = meta.asset_symbol || 'XAU/USD';
    const logo = meta.asset_logo || 'Au';

    const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };

    const cls = assetClass();
    const nonMetal = cls !== 'metal';

    const subtitle = cls === 'crypto' ? `${sym} · 24/7 Crypto · Institutional Desk`
        : cls === 'index' ? `${sym} · Equity Index · Institutional Desk`
        : cls === 'commodity' ? `${sym} · Commodity Futures · Institutional Desk`
        : cls === 'stock' ? `${sym} · NSE Equity · Institutional Desk`
        : `${sym} & MCX ${m} · Institutional Desk`;

    document.title = `${m} Pre-Session Analysis | ${sym}`;
    set('hero-logo', logo);
    set('header-title', `${m} Pre-Session Analysis`);
    set('header-subtitle', subtitle);
    set('chart-title', `📈 ${m} Price Chart`);
    // FX-priced-in only makes sense for USD-quoted assets.
    set('scenarios-title', (meta.currency || '$') === '$' ? `🌍 Scenarios & ${m} in FX` : `🌍 ${m} Scenarios`);
    set('footer-text',
        `${m} Pre-Session Analysis Dashboard · Data from yfinance & Quant Research Pipeline · ` +
        `For educational & research purposes only · Not financial advice`);

    // Metals-only panels: MCX/India card is hidden for crypto & indices, and
    // the Session row collapses to a single full-width column.
    const mcxCard = document.getElementById('mcx-card');
    const sessionRow = document.getElementById('session-row');
    if (mcxCard) mcxCard.style.display = nonMetal ? 'none' : '';
    if (sessionRow) sessionRow.style.gridTemplateColumns = nonMetal ? '1fr' : '';
    if (!nonMetal) set('mcx-title', `🇮🇳 MCX ${m} — India`);

    // Reflect active state across the grouped nav: highlight the selected
    // asset, highlight its category, and show the asset name in that trigger.
    document.querySelectorAll('#asset-nav .asset-group').forEach(group => {
        let activeBtn = null;
        group.querySelectorAll('.asset-btn').forEach(btn => {
            const on = btn.dataset.asset === currentAsset;
            btn.classList.toggle('active', on);
            if (on) activeBtn = btn;
        });
        group.classList.toggle('active', !!activeBtn);
        const sel = group.querySelector('.gt-sel');
        if (sel) sel.textContent = activeBtn ? '· ' + (ASSET_SHORT[currentAsset] || metal()) : '';
    });
}

// Short labels shown in a category trigger when one of its assets is active.
const ASSET_SHORT = {
    gold: 'Gold', silver: 'Silver',
    bitcoin: 'BTC', ethereum: 'ETH', solana: 'SOL', bnb: 'BNB', xrp: 'XRP',
    sp500: 'S&P 500', nasdaq: 'Nasdaq',
};

let assetToggleWired = false;
function closeAssetMenus() {
    document.querySelectorAll('#asset-nav .asset-group.open').forEach(g => g.classList.remove('open'));
}
function setupAssetToggle() {
    if (assetToggleWired) return;           // wire once; survives re-renders
    const nav = document.getElementById('asset-nav');
    if (!nav) return;

    // Category dropdown triggers — open one menu at a time.
    nav.querySelectorAll('.asset-group').forEach(group => {
        const trigger = group.querySelector('.group-trigger');
        if (trigger) trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const wasOpen = group.classList.contains('open');
            closeAssetMenus();
            if (!wasOpen) group.classList.add('open');
        });
    });

    // Asset selection.
    nav.querySelectorAll('.asset-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAssetMenus();
            const asset = btn.dataset.asset;
            if (asset !== currentAsset) loadData(asset);
        });
    });

    // Click outside closes any open menu.
    document.addEventListener('click', closeAssetMenus);
    assetToggleWired = true;
}

// ═══════════════════════════════════════
// HEADER
// ═══════════════════════════════════════
function renderHeader() {
    const tech = DATA.technical;
    const session = DATA.session_plan;
    
    // Price
    const price = tech.current_price;
    document.getElementById('hero-price').textContent = price ? `${cur()}${price.toFixed(2)}` : '$---';
    
    // Change
    const change = tech.daily_change || 0;
    const changePct = tech.daily_change_pct || 0;
    const changeEl = document.getElementById('hero-change');
    changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePct >= 0 ? '+' : ''}${changePct.toFixed(3)}%)`;
    changeEl.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');
    
    // Session
    document.getElementById('active-session').textContent = session.active_session || 'Off-Hours';
    
    // Timestamp
    const meta = DATA.meta;
    document.getElementById('timestamp').textContent = meta.generated_at ? meta.generated_at.substring(0, 19) : '--';
}

// ═══════════════════════════════════════
// COMPOSITE SIGNAL BAR
// ═══════════════════════════════════════
function renderSignalBar() {
    const sig = DATA.composite_signal;
    
    // Signal value
    const signalVal = sig.signal || 0;
    const valEl = document.getElementById('signal-value');
    valEl.textContent = (signalVal >= 0 ? '+' : '') + signalVal.toFixed(4);
    valEl.style.color = signalVal > 0.05 ? 'var(--green)' : signalVal < -0.05 ? 'var(--red)' : 'var(--amber)';
    
    // Emoji
    document.getElementById('signal-emoji').textContent = sig.emoji || '⚪';
    
    // Gauge
    const gauge = document.getElementById('signal-gauge');
    const pct = ((signalVal + 1) / 2) * 100;
    const gaugeColor = signalVal > 0.1 ? 'var(--green)' : signalVal < -0.1 ? 'var(--red)' : 'var(--amber)';
    gauge.style.setProperty('--gauge-pct', pct + '%');
    gauge.style.setProperty('--gauge-color', gaugeColor);
    
    // Action
    const actionEl = document.getElementById('signal-action');
    actionEl.textContent = sig.action || '--';
    if (sig.action?.includes('BUY')) {
        actionEl.style.background = 'var(--green-bg)';
        actionEl.style.color = 'var(--green)';
    } else if (sig.action?.includes('SELL')) {
        actionEl.style.background = 'var(--red-bg)';
        actionEl.style.color = 'var(--red)';
    } else {
        actionEl.style.background = 'var(--amber-bg)';
        actionEl.style.color = 'var(--amber)';
    }
    
    // Confidence
    document.getElementById('signal-confidence').textContent = 
        ((sig.confidence || 0) * 100).toFixed(1) + '%';
    
    // Regime — semantic color by label (green=bullish, red=bearish, yellow=neutral)
    const regimeEl = document.getElementById('signal-regime');
    const regimeTxt = sig.regime || '--';
    regimeEl.textContent = regimeTxt;
    regimeEl.style.color = regimeTxt.includes('BULLISH') ? 'var(--green)'
        : regimeTxt.includes('BEARISH') ? 'var(--red)' : 'var(--amber)';
    
    // Breakdown
    const breakdownEl = document.getElementById('signal-breakdown');
    breakdownEl.innerHTML = '';
    
    if (sig.breakdown) {
        const items = ['technical', 'macro', 'sentiment', 'volatility', 'correlation', 'ml', 'seasonality'];
        items.forEach(key => {
            const b = sig.breakdown[key];
            if (!b) return;
            
            const div = document.createElement('div');
            div.className = 'breakdown-item';
            const norm = b.normalized || 0;
            const color = norm > 0.05 ? 'var(--green)' : norm < -0.05 ? 'var(--red)' : 'var(--amber)';
            div.innerHTML = `
                <div class="label">${key}</div>
                <div class="value" style="color:${color}">${norm >= 0 ? '+' : ''}${norm.toFixed(3)}</div>
                <div class="sub">${(b.weight * 100).toFixed(0)}% weight</div>
            `;
            breakdownEl.appendChild(div);
        });
    }
}

// ═══════════════════════════════════════
// CANDLESTICK CHART
// ═══════════════════════════════════════
function renderChart(timeframe) {
    currentTf = timeframe;
    const container = document.getElementById('price-chart');
    container.innerHTML = '';
    
    const candles = DATA.technical.candlestick_data?.[timeframe];
    if (!candles || candles.length === 0) {
        container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:60px;">No chart data available</div>';
        return;
    }
    
    const tc = themeColors();
    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 400,
        layout: {
            background: { type: 'solid', color: tc.bg },
            textColor: tc.text,
            fontSize: 11,
            fontFamily: 'Inter, sans-serif',
        },
        grid: {
            vertLines: { color: tc.grid },
            horzLines: { color: tc.grid },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: { color: 'rgba(76, 194, 255, 0.25)', labelBackgroundColor: '#4CC2FF' },
            horzLine: { color: 'rgba(76, 194, 255, 0.25)', labelBackgroundColor: '#4CC2FF' },
        },
        timeScale: {
            borderColor: tc.border,
            timeVisible: timeframe === '1h',
        },
        rightPriceScale: {
            borderColor: tc.border,
        },
    });
    
    candleSeries = chart.addCandlestickSeries({
        upColor: '#3FB950',
        downColor: '#F85149',
        borderUpColor: '#3FB950',
        borderDownColor: '#F85149',
        wickUpColor: '#3FB950',
        wickDownColor: '#F85149',
    });
    
    candleSeries.setData(candles);

    // Pivot/Fib/SMA overlays are 1-year-scale — only meaningful on the
    // short-range views, not the multi-decade Max / 30Y charts.
    if (timeframe === 'daily' || timeframe === '1h') addChartLevels(timeframe);

    chart.timeScale().fitContent();
    
    // Resize handler
    const resizeObserver = new ResizeObserver(() => {
        chart.applyOptions({ width: container.clientWidth });
    });
    resizeObserver.observe(container);
}

function addChartLevels(timeframe) {
    if (!candleSeries) return;
    
    const fib = DATA.technical.fibonacci || {};
    const pivots = DATA.technical.pivot_points?.classic || {};
    
    // Add SMA lines
    const tf = DATA.technical.timeframes?.[timeframe];
    if (tf?.indicators) {
        const sma20 = tf.indicators.SMA_20;
        const sma50 = tf.indicators.SMA_50;
        if (sma20) {
            const line1 = candleSeries.createPriceLine({
                price: sma20, color: '#4CC2FF', lineWidth: 1, lineStyle: 2,
                title: 'SMA 20', axisLabelVisible: false,
            });
        }
        if (sma50) {
            const line2 = candleSeries.createPriceLine({
                price: sma50, color: '#8AD7FF', lineWidth: 1, lineStyle: 2,
                title: 'SMA 50', axisLabelVisible: false,
            });
        }
    }
    
    // Pivot point
    if (pivots.PP) {
        candleSeries.createPriceLine({
            price: pivots.PP, color: '#4CC2FF', lineWidth: 1, lineStyle: 0,
            title: 'PP', axisLabelVisible: true,
        });
    }
    if (pivots.R1) {
        candleSeries.createPriceLine({
            price: pivots.R1, color: '#F85149', lineWidth: 1, lineStyle: 2,
            title: 'R1', axisLabelVisible: true,
        });
    }
    if (pivots.S1) {
        candleSeries.createPriceLine({
            price: pivots.S1, color: '#3FB950', lineWidth: 1, lineStyle: 2,
            title: 'S1', axisLabelVisible: true,
        });
    }
}

function setupChartTabs() {
    document.querySelectorAll('#chart-tabs .chart-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#chart-tabs .chart-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderChart(tab.dataset.tf);
        });
    });
}

// ═══════════════════════════════════════
// KEY LEVELS
// ═══════════════════════════════════════
function renderKeyLevels() {
    const levels = DATA.technical.key_levels || {};
    const container = document.getElementById('key-levels');
    
    const items = [
        { label: '52-Week High', value: levels['52w_high'], type: 'resistance' },
        { label: 'Resistance 1 (20d)', value: levels.resistance_1, type: 'resistance' },
        { label: 'Support 1 (20d)', value: levels.support_1, type: 'support' },
        { label: '52-Week Low', value: levels['52w_low'], type: 'support' },
    ];
    
    container.innerHTML = items.map(item => `
        <div class="level-item level-${item.type}">
            <span class="level-label">${item.label}</span>
            <span class="level-value ${item.type === 'resistance' ? 'text-red' : 'text-green'}">
                ${cur()}${item.value?.toFixed(2) || '--'}
            </span>
        </div>
    `).join('');
    
    // Distance info
    if (levels.dist_from_high_pct != null) {
        container.innerHTML += `
            <div style="margin-top:8px; font-size:0.7rem; color:var(--text-muted);">
                Distance from 52w High: ${levels.dist_from_high_pct}% · 
                From 52w Low: +${levels.dist_from_low_pct}%
            </div>
        `;
    }
    
    // Fibonacci
    const fib = DATA.technical.fibonacci || {};
    const fibContainer = document.getElementById('fib-levels');
    const fibItems = [
        { label: 'Swing High (0%)', value: fib.fib_0 },
        { label: 'Fib 23.6%', value: fib.fib_236 },
        { label: 'Fib 38.2%', value: fib.fib_382 },
        { label: 'Fib 50.0%', value: fib.fib_500 },
        { label: 'Fib 61.8%', value: fib.fib_618 },
        { label: 'Fib 78.6%', value: fib.fib_786 },
        { label: 'Swing Low (100%)', value: fib.fib_100 },
    ];
    
    fibContainer.innerHTML = fibItems.map(item => `
        <div class="level-item level-fib">
            <span class="level-label">${item.label}</span>
            <span class="level-value text-gold">${cur()}${item.value?.toFixed(2) || '--'}</span>
        </div>
    `).join('');
}

// ═══════════════════════════════════════
// TECHNICAL SCORECARD
// ═══════════════════════════════════════
function renderTechnicalScorecard() {
    const tfs = DATA.technical.timeframes || {};
    const container = document.getElementById('technical-scorecard');
    
    // Overall badge
    const badge = document.getElementById('tech-bias-badge');
    const overall = DATA.technical.overall_bias || 'Neutral';
    badge.textContent = `${overall} (${DATA.technical.overall_score || 0})`;
    badge.style.color = overall.includes('Bullish') ? 'var(--green)' : overall.includes('Bearish') ? 'var(--red)' : 'var(--amber)';
    badge.style.background = overall.includes('Bullish') ? 'var(--green-bg)' : overall.includes('Bearish') ? 'var(--red-bg)' : 'var(--amber-bg)';
    
    // Build timeframe tables
    let html = '';
    
    for (const [tfName, tfData] of Object.entries(tfs)) {
        const score = tfData.score || 0;
        const bias = tfData.bias || 'Neutral';
        const biasColor = bias.includes('Bullish') ? 'var(--green)' : bias.includes('Bearish') ? 'var(--red)' : 'var(--amber)';
        
        html += `
            <div style="margin-bottom:14px;">
                <div class="flex-between mb-1">
                    <span style="font-size:0.75rem; font-weight:600; text-transform:uppercase;">${tfName}</span>
                    <span class="font-mono" style="font-size:0.75rem; font-weight:600; color:${biasColor};">${bias} (${score})</span>
                </div>
                <table class="indicator-table">
                    <thead>
                        <tr><th>Indicator</th><th>Value</th><th>Signal</th></tr>
                    </thead>
                    <tbody>`;
        
        // Key indicators
        const indicators = tfData.indicators || {};
        const signals = tfData.signals || {};
        
        const rows = [
            { name: 'RSI (14)', value: indicators.RSI_14, signal: signals.rsi },
            { name: 'MACD', value: indicators.MACD_Histogram, signal: signals.macd },
            { name: 'Bollinger', value: indicators.BB_Position, signal: signals.bollinger },
            { name: 'ATR (14)', value: indicators.ATR_14, signal: null },
            { name: 'Volume', value: indicators.Volume_Ratio, signal: signals.volume },
            { name: 'SMA 20', value: indicators.SMA_20, signal: null },
            { name: 'SMA 50', value: indicators.SMA_50, signal: null },
            { name: 'SMA 200', value: indicators.SMA_200, signal: null },
        ];
        
        rows.forEach(row => {
            if (row.value == null) return;
            const sigColor = getSignalColor(row.signal);
            html += `
                <tr>
                    <td style="color:var(--text-secondary)">${row.name}</td>
                    <td>${typeof row.value === 'number' ? row.value.toFixed(4) : row.value}</td>
                    <td style="color:${sigColor}">${row.signal || '—'}</td>
                </tr>`;
        });
        
        // Golden Cross
        if (signals.golden_cross != null) {
            html += `
                <tr>
                    <td style="color:var(--text-secondary)">Golden Cross</td>
                    <td>${signals.golden_cross ? '✓ Active' : '✗ No'}</td>
                    <td style="color:${signals.golden_cross ? 'var(--green)' : 'var(--red)'}">${signals.golden_cross ? 'Bullish' : 'Bearish'}</td>
                </tr>`;
        }
        
        html += `</tbody></table></div>`;
    }
    
    container.innerHTML = html || '<div class="text-muted">No technical data available</div>';
}

// ═══════════════════════════════════════
// MACRO ENVIRONMENT
// ═══════════════════════════════════════
function renderMacro() {
    const macro = DATA.macro || {};
    const container = document.getElementById('macro-factors');
    const badge = document.getElementById('macro-regime-badge');
    
    badge.textContent = `${macro.regime || 'N/A'} (${macro.composite_score || 0})`;
    const regimeColor = macro.composite_score > 0 ? 'var(--green)' : macro.composite_score < 0 ? 'var(--red)' : 'var(--amber)';
    badge.style.color = regimeColor;
    badge.style.background = macro.composite_score > 0 ? 'var(--green-bg)' : macro.composite_score < 0 ? 'var(--red-bg)' : 'var(--amber-bg)';
    
    const factors = macro.factors || {};
    let html = '';

    // ── Macro tilt gauge ──
    const cs = macro.composite_score || 0;
    const maxp = macro.max_possible || 18;
    const tiltPct = Math.max(0, Math.min(100, ((cs + maxp) / (2 * maxp)) * 100));
    // Risk-on assets (crypto, indices): frame the gauge as financial conditions
    // / risk, not a metals-style "bullish/bearish" call from safe-haven logic.
    const riskOn = !isMetal();
    const leftLbl = riskOn ? 'Risk-Off' : `Bearish ${metal()}`;
    const rightLbl = riskOn ? 'Risk-On' : `Bullish ${metal()}`;
    const midLbl = riskOn ? 'Financial Conditions' : 'Macro Tilt';
    html += `
        <div style="margin-bottom:12px;">
            <div class="flex-between" style="font-size:0.62rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">
                <span>${leftLbl}</span><span>${midLbl}</span><span>${rightLbl}</span>
            </div>
            <div style="position:relative; height:10px; background:linear-gradient(90deg, var(--red), var(--bg-elevated), var(--green)); border-radius:6px;">
                <div style="position:absolute; top:-3px; left:${tiltPct}%; transform:translateX(-50%); width:4px; height:16px; background:var(--text-highlight); border-radius:2px; box-shadow:0 0 6px rgba(0,0,0,0.6);"></div>
            </div>
            <div style="text-align:center; font-size:0.7rem; margin-top:6px; color:${regimeColor};">${cs >= 0 ? '+' : ''}${cs} / ±${maxp} composite</div>
        </div>
    `;

    // ── Key macro readings tiles ──
    const readings = [
        { k: 'DXY', v: factors.DXY?.value, fmt: v => v?.toFixed(1) },
        { k: 'VIX', v: factors.VIX?.value, fmt: v => v?.toFixed(1) },
        { k: '10Y Yield', v: factors.Yields?.value, fmt: v => v?.toFixed(2) + '%' },
        { k: 'Curve 10-2', v: factors.Yield_Curve?.value, fmt: v => (v >= 0 ? '+' : '') + v?.toFixed(2) + '%' },
    ].filter(r => r.v != null);
    if (readings.length) {
        html += `<div class="fx-grid" style="margin-bottom:12px;">${readings.map(r => `
            <div class="fx-cell"><div class="fx-cur">${r.k}</div><div class="fx-val">${r.fmt(r.v)}</div></div>`).join('')}</div>`;
    }

    if (!isMetal()) {
        html += `<div style="font-size:0.62rem; color:var(--text-muted); background:var(--bg-elevated); border-radius:var(--radius-xs); padding:7px 9px; margin-bottom:10px; border-left:3px solid var(--amber);">
            Read as a USD / rates / risk backdrop, not a safe-haven call. ${metal()} is risk-on: easy conditions (weak USD, low yields, low VIX) are a tailwind; spikes in fear are a headwind.</div>`;
    }

    for (const [name, factor] of Object.entries(factors)) {
        const score = factor.score || 0;
        const cls = score > 0 ? 'bullish' : score < 0 ? 'bearish' : 'neutral';
        const scoreColor = score > 0 ? 'var(--green)' : score < 0 ? 'var(--red)' : 'var(--amber)';
        const scoreBg = score > 0 ? 'var(--green-bg)' : score < 0 ? 'var(--red-bg)' : 'var(--amber-bg)';
        
        html += `
            <div class="macro-factor ${cls}">
                <div class="macro-factor-header">
                    <span class="macro-factor-name">${name.replace('_', ' ')}</span>
                    <span class="macro-factor-score" style="color:${scoreColor};background:${scoreBg}">${score > 0 ? '+' : ''}${score}</span>
                </div>
                <div class="macro-factor-detail">${factor.detail || ''}</div>
            </div>
        `;
    }
    
    container.innerHTML = html || '<div class="text-muted">No macro data</div>';
}

// ═══════════════════════════════════════
// SENTIMENT
// ═══════════════════════════════════════
function renderSentiment() {
    const sent = DATA.sentiment || {};
    const container = document.getElementById('sentiment-meter');
    const badge = document.getElementById('sentiment-badge');
    
    badge.textContent = sent.composite_label || 'N/A';
    const score = sent.composite_score || 0;
    badge.style.color = score > 0.05 ? 'var(--green)' : score < -0.05 ? 'var(--red)' : 'var(--amber)';
    badge.style.background = score > 0.05 ? 'var(--green-bg)' : score < -0.05 ? 'var(--red-bg)' : 'var(--amber-bg)';
    
    let html = '';
    
    // Fear & Greed
    const fg = sent.fear_greed || {};
    if (fg.score != null) {
        const fgPct = fg.score;
        const fgColor = fgPct <= 30 ? 'var(--red)' : fgPct >= 70 ? 'var(--green)' : 'var(--amber)';
        html += `
            <div class="sentiment-row">
                <span class="sentiment-label">Fear & Greed</span>
                <div class="sentiment-bar-track">
                    <div class="sentiment-bar-fill" style="width:${fgPct}%; background:linear-gradient(90deg, var(--red), var(--amber), var(--green));">
                        ${fgPct.toFixed(0)}
                    </div>
                </div>
            </div>
            <div style="font-size:0.7rem; color:var(--text-muted); margin-left:112px; margin-bottom:8px;">${fg.label || ''} — ${fg.gold_implication || ''}</div>
        `;
    }
    
    // News Sentiment
    const ns = sent.news_sentiment || {};
    if (ns.gold_sentiment != null) {
        const nsPct = ((ns.gold_sentiment + 1) / 2) * 100;
        html += `
            <div class="sentiment-row">
                <span class="sentiment-label">News Sentiment</span>
                <div class="sentiment-bar-track">
                    <div class="sentiment-bar-fill" style="width:${nsPct}%; background:${nsPct > 55 ? 'var(--green)' : nsPct < 45 ? 'var(--red)' : 'var(--amber)'};">
                        ${ns.gold_sentiment.toFixed(3)}
                    </div>
                </div>
            </div>
            <div style="font-size:0.65rem; color:var(--text-muted); margin-left:112px; margin-bottom:8px;">${ns.article_count || 0} market news articles analyzed</div>
        `;
    }
    
    // Composite
    const compPct = ((score + 1) / 2) * 100;
    html += `
        <div class="sentiment-row" style="margin-top:8px;">
            <span class="sentiment-label" style="font-weight:600;">Composite</span>
            <div class="sentiment-bar-track">
                <div class="sentiment-bar-fill" style="width:${compPct}%; background:${score > 0.05 ? 'var(--green)' : score < -0.05 ? 'var(--red)' : 'var(--amber)'};">
                    ${score >= 0 ? '+' : ''}${score.toFixed(4)}
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Headlines
    const headlinesContainer = document.getElementById('news-headlines');
    const headlines = ns.headlines || [];
    if (headlines.length > 0) {
        headlinesContainer.innerHTML = `
            <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">Market Headlines</div>
            ${headlines.map(h => {
                const sc = h.sentiment || 0;
                const borderColor = sc > 0.1 ? 'var(--green)' : sc < -0.1 ? 'var(--red)' : 'var(--amber)';
                return `
                    <div class="headline-item" style="border-left-color:${borderColor}">
                        <div class="headline-title">${h.title}</div>
                        <span class="headline-sentiment" style="color:${borderColor}">${sc >= 0 ? '+' : ''}${sc.toFixed(3)}</span>
                    </div>
                `;
            }).join('')}
        `;
    }
}

// ═══════════════════════════════════════
// CORRELATION HEATMAP
// ═══════════════════════════════════════
function renderCorrelation() {
    const corr = DATA.correlation || {};
    const container = document.getElementById('corr-heatmap');
    const badge = document.getElementById('corr-regime-badge');
    
    badge.textContent = corr.regime || 'N/A';
    badge.style.color = 'var(--blue)';
    badge.style.background = 'var(--blue-bg)';
    
    const matrix = corr.matrix || [];
    
    if (matrix.length === 0) {
        container.innerHTML = '<div class="text-muted">No correlation data</div>';
        return;
    }
    
    let html = '';
    matrix.forEach(item => {
        const c = item.correlation;
        const width = Math.abs(c) * 100;
        const color = c > 0 ? `rgba(0, 200, 83, ${Math.min(Math.abs(c) + 0.2, 1)})` 
                            : `rgba(255, 23, 68, ${Math.min(Math.abs(c) + 0.2, 1)})`;
        const textColor = Math.abs(c) > 0.3 ? 'white' : 'var(--text-primary)';
        
        html += `
            <div class="heatmap-row">
                <span class="heatmap-label">${item.asset}</span>
                <div class="heatmap-bar-container">
                    <div class="heatmap-bar" style="width:${Math.max(width, 15)}%; background:${color}; color:${textColor};">
                        ${c >= 0 ? '+' : ''}${c.toFixed(3)}
                    </div>
                    <span style="font-size:0.6rem; color:var(--text-muted);">${item.strength}</span>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Divergence alerts
    const divContainer = document.getElementById('corr-divergences');
    const divs = corr.divergences || [];
    if (divs.length > 0) {
        divContainer.innerHTML = `
            <div style="margin-top:8px; padding:8px 10px; background:var(--amber-bg); border-radius:var(--radius-xs); border-left:3px solid var(--amber);">
                <div style="font-size:0.7rem; font-weight:600; color:var(--amber); margin-bottom:4px;">⚠ Correlation Divergences</div>
                ${divs.map(d => `<div style="font-size:0.65rem; color:var(--text-secondary);">${d.alert}</div>`).join('')}
            </div>
        `;
    }
}

// ═══════════════════════════════════════
// VOLATILITY
// ═══════════════════════════════════════
function renderVolatility() {
    const vol = DATA.volatility || {};
    const container = document.getElementById('vol-bars');
    const badge = document.getElementById('vol-regime-badge');
    
    badge.textContent = vol.regime || 'N/A';
    const volScore = vol.vol_score || 0;
    badge.style.color = volScore > 0 ? 'var(--red)' : volScore < 0 ? 'var(--green)' : 'var(--amber)';
    badge.style.background = volScore > 0 ? 'var(--red-bg)' : volScore < 0 ? 'var(--green-bg)' : 'var(--amber-bg)';
    
    const hv = vol.historical_vol || {};
    let html = '';
    
    const volItems = [
        { label: '5-Day HV', value: hv['5d'] },
        { label: '10-Day HV', value: hv['10d'] },
        { label: '20-Day HV', value: hv['20d'] },
        { label: '60-Day HV', value: hv['60d'] },
        { label: '120-Day HV', value: hv['120d'] },
        { label: 'Parkinson 21d', value: hv['parkinson_21d'] },
    ];
    
    volItems.forEach(item => {
        if (item.value == null) return;
        const pct = Math.min(item.value / 40 * 100, 100);
        html += `
            <div class="vol-bar-container">
                <div class="vol-bar-label">
                    <span>${item.label}</span>
                    <span class="vol-value">${item.value.toFixed(2)}%</span>
                </div>
                <div class="vol-bar">
                    <div class="vol-bar-fill" style="width:${pct}%;"></div>
                </div>
            </div>
        `;
    });
    
    // Vol percentile
    if (vol.vol_percentile != null) {
        html += `
            <div class="vol-percentile-gauge">
                <div class="vol-percentile-value">${vol.vol_percentile.toFixed(0)}th</div>
                <div>
                    <div style="font-size:0.75rem; font-weight:600;">Volatility Percentile</div>
                    <div class="vol-percentile-label">Current vol rank vs 1-year history</div>
                </div>
            </div>
        `;
    }
    
    // Term structure
    html += `
        <div style="margin-top:10px; font-size:0.75rem; color:var(--text-secondary);">
            <strong style="color:var(--text-primary);">Term Structure:</strong> ${vol.term_structure || 'N/A'}
        </div>
    `;
    
    container.innerHTML = html;
    
    // Expected range
    const rangeContainer = document.getElementById('vol-expected-range');
    const range = vol.expected_range || {};
    if (range.atr_14) {
        rangeContainer.innerHTML = `
            <div style="padding:10px; background:var(--bg-elevated); border-radius:var(--radius-xs);">
                <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:6px;">Expected Daily Range (ATR-14)</div>
                <div class="flex-between">
                    <span class="text-green font-mono" style="font-size:0.85rem;">${cur()}${range.expected_low?.toFixed(2)}</span>
                    <span class="text-gold font-mono font-bold" style="font-size:0.85rem;">${cur()}${range.atr_14?.toFixed(2)}</span>
                    <span class="text-red font-mono" style="font-size:0.85rem;">${cur()}${range.expected_high?.toFixed(2)}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.6rem; color:var(--text-muted); margin-top:2px;">
                    <span>Expected Low</span>
                    <span>ATR (${range.atr_pct?.toFixed(2)}%)</span>
                    <span>Expected High</span>
                </div>
            </div>
        `;
    }
}

// ═══════════════════════════════════════
// ICHIMOKU
// ═══════════════════════════════════════
function renderIchimoku() {
    const ich = DATA.technical.ichimoku || {};
    const container = document.getElementById('ichimoku-data');
    
    if (Object.keys(ich).length === 0) {
        container.innerHTML = '<div class="text-muted">Insufficient data for Ichimoku</div>';
        return;
    }
    
    const items = [
        { label: 'Tenkan-sen (9)', value: ich.tenkan_sen },
        { label: 'Kijun-sen (26)', value: ich.kijun_sen },
        { label: 'Senkou Span A', value: ich.senkou_span_a },
        { label: 'Senkou Span B', value: ich.senkou_span_b },
        { label: 'TK Cross', value: ich.tk_cross, isSignal: true },
        { label: 'Cloud Position', value: ich.cloud_position, isSignal: true },
    ];
    
    container.innerHTML = items.map(item => {
        if (item.value == null) return '';
        const color = item.isSignal 
            ? (String(item.value).includes('Bullish') ? 'var(--green)' : String(item.value).includes('Bearish') ? 'var(--red)' : 'var(--amber)')
            : 'var(--gold-light)';
        return `
            <div class="ichimoku-item">
                <span style="font-size:0.75rem; color:var(--text-secondary);">${item.label}</span>
                <span class="font-mono" style="font-size:0.8rem; font-weight:600; color:${color};">
                    ${item.isSignal ? item.value : cur() +item.value?.toFixed(2)}
                </span>
            </div>
        `;
    }).join('');
}

// ═══════════════════════════════════════
// PIVOT POINTS
// ═══════════════════════════════════════
function renderPivotPoints(type) {
    const pivots = DATA.technical.pivot_points?.[type] || {};
    const container = document.getElementById('pivot-points');
    
    if (Object.keys(pivots).length === 0) {
        container.innerHTML = '<div class="text-muted">No pivot data</div>';
        return;
    }
    
    // Sort: R3, R2, R1, PP, S1, S2, S3 (or R4..S4 for Camarilla)
    const order = type === 'classic' 
        ? ['R3', 'R2', 'R1', 'PP', 'S1', 'S2', 'S3']
        : ['R4', 'R3', 'R2', 'R1', 'S1', 'S2', 'S3', 'S4'];
    
    container.innerHTML = order.map(key => {
        const val = pivots[key];
        if (val == null) return '';
        
        const levelType = key === 'PP' ? 'pivot' : key.startsWith('R') ? 'resistance' : 'support';
        const color = levelType === 'resistance' ? 'text-red' : levelType === 'support' ? 'text-green' : 'text-gold';
        
        return `
            <div class="level-item level-${levelType}">
                <span class="level-label">${key}</span>
                <span class="level-value ${color}">${cur()}${val.toFixed(2)}</span>
            </div>
        `;
    }).join('');
}

function setupPivotTabs() {
    document.querySelectorAll('#pivot-tabs .chart-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#pivot-tabs .chart-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderPivotPoints(tab.dataset.pivot);
        });
    });
}

// ═══════════════════════════════════════
// SESSION PLAN
// ═══════════════════════════════════════
function renderSessionPlan() {
    const plan = DATA.session_plan || {};
    const container = document.getElementById('session-plans');
    const sessions = plan.sessions || {};
    const activeSession = plan.active_session || '';
    
    let html = '';
    
    // Session info header
    html += `
        <div style="margin-bottom:12px; font-size:0.7rem; color:var(--text-muted);">
            ${plan.current_time_ist || ''} · 
            Next: ${plan.next_session?.name || 'N/A'} (in ${plan.next_session?.hours_until || '--'}h)
        </div>
    `;
    
    for (const [name, session] of Object.entries(sessions)) {
        const isActive = name === activeSession;
        html += `
            <div class="session-card ${isActive ? 'active-session' : ''}">
                <div class="session-card-header">
                    <span class="session-name">${isActive ? '⚡ ' : ''}${name}</span>
                    <span class="session-vol-rank">${session.volatility_rank || ''}</span>
                </div>
                <div class="session-bias">${session.bias || ''}</div>
                <div class="session-strategy">${session.strategy || ''}</div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// ═══════════════════════════════════════
// MCX GOLD — INDIA
// ═══════════════════════════════════════
function renderMCX() {
    const mcx = DATA.session_plan?.mcx_gameplan || {};
    const container = document.getElementById('mcx-data');
    
    let html = '';
    
    // MCX equivalent (per quoted unit: 10g for gold, kg for silver)
    if (mcx.mcx_gold_equivalent) {
        html += `
            <div class="mcx-highlight">
                <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">MCX ${metal()} Equivalent (per ${mcx.mcx_unit_label || '10g'})</div>
                <div class="mcx-price">₹${Number(mcx.mcx_gold_equivalent).toLocaleString('en-IN')}</div>
                <div class="mcx-conversion">${mcx.conversion_note || ''}</div>
            </div>
        `;
    }
    
    // USD/INR
    html += `
        <div style="display:flex; gap:12px; margin-bottom:12px;">
            <div class="risk-item" style="flex:1;">
                <div class="label">USD/INR</div>
                <div class="value text-gold">${mcx.usdinr_rate?.toFixed(2) || '--'}</div>
            </div>
    `;
    
    // NSE ETF proxy (GOLDBEES / SILVERBEES)
    if (mcx.goldbees_price) {
        html += `
            <div class="risk-item" style="flex:1;">
                <div class="label">${mcx.proxy_label || 'GOLDBEES'}</div>
                <div class="value">₹${mcx.goldbees_price?.toFixed(2)}</div>
            </div>
        `;
    }
    html += `</div>`;
    
    // India bias
    if (mcx.india_bias) {
        const biasColor = mcx.india_bias.includes('Bullish') ? 'var(--green)' : mcx.india_bias.includes('Bearish') ? 'var(--red)' : 'var(--amber)';
        html += `
            <div style="padding:8px 12px; background:var(--bg-elevated); border-radius:var(--radius-xs); margin-bottom:10px; border-left:3px solid ${biasColor};">
                <div style="font-size:0.75rem; color:${biasColor}; font-weight:600;">${mcx.india_bias}</div>
            </div>
        `;
    }
    
    // Session info
    html += `<div style="font-size:0.7rem; color:var(--text-muted); margin-bottom:8px;">Session: ${mcx.session_times || ''}</div>`;
    
    // Key factors
    if (mcx.key_factors) {
        html += `
            <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">India Market Factors</div>
            <ul class="mcx-factors">
                ${mcx.key_factors.map(f => `<li>${f}</li>`).join('')}
            </ul>
        `;
    }
    
    container.innerHTML = html || '<div class="text-muted">No MCX data available</div>';
}

// ═══════════════════════════════════════
// TRADE SETUPS
// ═══════════════════════════════════════
function renderTradeSetups() {
    const setups = DATA.session_plan?.trade_setups || [];
    const container = document.getElementById('trade-setups');
    const sig = DATA.composite_signal || {};
    const price = DATA.technical?.current_price;
    const zones = DATA.structure?.confluence_zones || [];

    // ── Always-on context: bias + nearest trigger levels ──
    const nearestRes = zones.filter(z => z.side === 'resistance').sort((a, b) => a.dist_pct - b.dist_pct)[0];
    const nearestSup = zones.filter(z => z.side === 'support').sort((a, b) => b.dist_pct - a.dist_pct)[0];
    const actColor = sig.action?.includes('BUY') ? 'var(--green)' : sig.action?.includes('SELL') ? 'var(--red)' : 'var(--amber)';
    let contextHtml = `
        <div style="padding:10px; background:var(--bg-elevated); border-radius:var(--radius-xs); margin-bottom:10px;">
            <div class="flex-between" style="margin-bottom:6px;">
                <span style="font-size:0.7rem; color:var(--text-muted);">Bias</span>
                <span style="font-size:0.78rem; font-weight:700; color:${actColor};">${sig.action || '--'} · ${((sig.confidence || 0) * 100).toFixed(0)}%</span>
            </div>
            <div class="trade-levels" style="margin:0;">
                <div class="trade-level"><div class="label">Break Above</div><div class="price text-green">${nearestRes ? cur() +nearestRes.center.toFixed(0) : '—'}</div></div>
                <div class="trade-level"><div class="label">Spot</div><div class="price text-gold">${price ? cur() +price.toFixed(0) : '—'}</div></div>
                <div class="trade-level"><div class="label">Break Below</div><div class="price text-red">${nearestSup ? cur() +nearestSup.center.toFixed(0) : '—'}</div></div>
            </div>
        </div>`;

    if (setups.length === 0) {
        container.innerHTML = contextHtml +
            `<div class="text-muted" style="font-size:0.72rem;">No high-conviction setup right now — composite signal is too weak/neutral for a directional entry. Trade the trigger levels above with confirmation, or stand aside.</div>`;
        return;
    }

    container.innerHTML = contextHtml + setups.map(setup => {
        const type = (setup.type || 'range').toLowerCase();
        
        let levelsHtml = '';
        if (setup.entry != null) {
            levelsHtml = `
                <div class="trade-levels">
                    <div class="trade-level">
                        <div class="label">Entry</div>
                        <div class="price text-gold">${cur()}${setup.entry?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Stop Loss</div>
                        <div class="price text-red">${cur()}${setup.stop_loss?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Target 1</div>
                        <div class="price text-green">${cur()}${setup.target_1?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Target 2</div>
                        <div class="price text-green">${cur()}${setup.target_2?.toFixed(2)}</div>
                    </div>
                </div>
            `;
        } else if (setup.buy_zone != null) {
            levelsHtml = `
                <div class="trade-levels">
                    <div class="trade-level">
                        <div class="label">Buy Zone</div>
                        <div class="price text-green">${cur()}${setup.buy_zone?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Sell Zone</div>
                        <div class="price text-red">${cur()}${setup.sell_zone?.toFixed(2)}</div>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="trade-setup ${type}">
                <div class="trade-setup-header">
                    <span class="trade-name">${setup.name || 'Setup'}</span>
                    <span class="trade-type ${type}">${setup.type || 'RANGE'}</span>
                </div>
                ${levelsHtml}
                <div style="font-size:0.7rem; color:var(--text-muted); margin-bottom:6px;">
                    R:R ${setup.risk_reward || 'N/A'} · Confidence: ${setup.confidence || '--'}%
                </div>
                <div class="trade-trigger">${setup.trigger || ''}</div>
            </div>
        `;
    }).join('');
}

// ═══════════════════════════════════════
// RISK PARAMETERS
// ═══════════════════════════════════════
function renderRiskParams() {
    const risk = DATA.session_plan?.risk_parameters || {};
    const container = document.getElementById('risk-params');
    
    let html = '';
    
    // ATR
    html += `
        <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px;">ATR-Based Risk Levels</div>
        <div class="risk-grid" style="margin-bottom:14px;">
            <div class="risk-item">
                <div class="label">ATR (14)</div>
                <div class="value text-gold">${cur()}${risk.atr_14?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">Tight Stop (0.5 ATR)</div>
                <div class="value text-red">${cur()}${risk.stop_tight?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">Normal Stop (1 ATR)</div>
                <div class="value text-red">${cur()}${risk.stop_normal?.toFixed(2) || '--'}</div>
            </div>
        </div>
    `;
    
    // Targets
    html += `
        <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px;">Target Distances</div>
        <div class="risk-grid" style="margin-bottom:14px;">
            <div class="risk-item">
                <div class="label">1R Target</div>
                <div class="value text-green">${cur()}${risk.target_1r?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">2R Target</div>
                <div class="value text-green">${cur()}${risk.target_2r?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">3R Target</div>
                <div class="value text-green">${cur()}${risk.target_3r?.toFixed(2) || '--'}</div>
            </div>
        </div>
    `;
    
    // Position sizing for account sizes
    const sizes = [10000, 50000, 100000];
    html += `<div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px;">Position Sizing (1% Risk)</div>`;
    
    html += `<table class="indicator-table"><thead><tr><th>Account</th><th>Risk/Trade</th><th>${risk.micro_label || ('Micro ' + metal())}</th><th>Standard</th></tr></thead><tbody>`;
    
    sizes.forEach(size => {
        const s = risk[`sizing_${size}`];
        if (!s) return;
        html += `
            <tr>
                <td>${cur()}${(size/1000)}K</td>
                <td>${cur()}${s.risk_per_trade_1pct?.toFixed(0)}</td>
                <td style="color:var(--gold-light)">${s.micro_gold_contracts?.toFixed(1)} lots</td>
                <td>${s.standard_gold_contracts?.toFixed(2)} lots</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    
    // MCX sizing
    if (risk.mcx_sizing) {
        html += `
            <div style="margin-top:12px; padding:8px 10px; background:var(--bg-elevated); border-radius:var(--radius-xs); border-left:3px solid var(--gold);">
                <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">🇮🇳 ${risk.mcx_sizing.mcx_name || ('MCX ' + metal())}</div>
                <div style="font-size:0.7rem; color:var(--text-secondary);">
                    Lot: ${risk.mcx_sizing.lot_size_mini} · Tick Value: ${risk.mcx_sizing.tick_value}
                </div>
                <div style="font-size:0.65rem; color:var(--text-muted); margin-top:2px;">${risk.mcx_sizing.note}</div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// ═══════════════════════════════════════
// MACHINE LEARNING
// ═══════════════════════════════════════
function renderML() {
    const ml = DATA.ml || {};
    const container = document.getElementById('ml-content');
    const badge = document.getElementById('ml-badge');

    if (!ml.available) {
        badge.textContent = 'N/A';
        container.innerHTML = `<div class="text-muted">ML model unavailable: ${ml.reason || 'insufficient data'}</div>`;
        return;
    }

    const pred = ml.prediction || {};
    const ens = ml.ensemble || {};
    const probUp = pred.prob_up || 50;
    const dirColor = pred.direction === 'UP' ? 'var(--green)' : 'var(--red)';

    badge.textContent = `${pred.direction} ${probUp}%`;
    badge.style.color = dirColor;
    badge.style.background = pred.direction === 'UP' ? 'var(--green-bg)' : 'var(--red-bg)';

    // Edge vs baseline
    const edge = ens.accuracy != null && ens.baseline_accuracy != null
        ? (ens.accuracy - ens.baseline_accuracy) : null;
    const edgeColor = edge > 0.5 ? 'var(--green)' : edge < -0.5 ? 'var(--red)' : 'var(--amber)';

    let html = `
        <div class="ml-prob-wrap">
            <div class="ml-dir" style="color:${dirColor}">${pred.direction === 'UP' ? '▲' : '▼'} ${pred.direction}</div>
            <div style="font-size:0.65rem; color:var(--text-muted);">Next session · ${pred.confidence}% conviction</div>
            <div class="ml-prob-bar">
                <div class="ml-prob-seg ml-prob-up" style="width:${probUp}%">${probUp}%</div>
                <div class="ml-prob-seg ml-prob-dn" style="width:${100 - probUp}%">${pred.prob_down}%</div>
            </div>
        </div>
        <div class="ml-metrics">
            <div class="ml-metric"><div class="label">OOS Accuracy</div><div class="value">${ens.accuracy ?? '--'}%</div></div>
            <div class="ml-metric"><div class="label">Baseline</div><div class="value">${ens.baseline_accuracy ?? '--'}%</div></div>
            <div class="ml-metric"><div class="label">ROC AUC</div><div class="value">${ens.auc ?? '--'}</div></div>
        </div>
        <div style="font-size:0.65rem; color:${edgeColor}; text-align:center; margin-bottom:8px;">
            ${edge != null ? (edge >= 0 ? '+' : '') + edge.toFixed(1) + '% edge over baseline' : ''}
            · Walk-forward validated on ${ml.samples} samples
        </div>
    `;

    // Per-model agreement
    if (pred.per_model) {
        html += `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">Model agreement (P up)</div>`;
        html += pred.per_model.map(m => `
            <div class="metric-row"><span class="k">${m.name}</span>
            <span class="v" style="color:${m.prob_up >= 50 ? 'var(--green)' : 'var(--red)'}">${m.prob_up}%</span></div>
        `).join('');
    }

    // Feature importance
    if (ml.feature_importance && ml.feature_importance.length) {
        const max = ml.feature_importance[0].importance || 1;
        html += `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin:10px 0 6px;">Top predictive features</div>`;
        html += ml.feature_importance.slice(0, 8).map(f => `
            <div class="feat-bar-row">
                <span class="feat-bar-label">${f.feature}</span>
                <div class="feat-bar-track"><div class="feat-bar-fill" style="width:${(f.importance / max * 100).toFixed(0)}%"></div></div>
                <span style="width:34px; text-align:right; color:var(--text-secondary)">${f.importance}%</span>
            </div>
        `).join('');
    }

    container.innerHTML = html;
}

// ═══════════════════════════════════════
// MONTE CARLO
// ═══════════════════════════════════════
function renderMonteCarlo() {
    const mc = DATA.montecarlo || {};
    const container = document.getElementById('mc-content');
    const badge = document.getElementById('mc-badge');

    if (!mc.available) {
        badge.textContent = 'N/A';
        container.innerHTML = '<div class="text-muted">Monte Carlo unavailable</div>';
        return;
    }

    badge.textContent = `P(up) ${mc.prob_up}%`;
    badge.style.color = mc.prob_up >= 50 ? 'var(--green)' : 'var(--red)';
    badge.style.background = mc.prob_up >= 50 ? 'var(--green-bg)' : 'var(--red-bg)';

    const p = mc.percentiles || {};
    let html = `
        <div style="font-size:0.65rem; color:var(--text-muted); margin-bottom:6px;">
            ${mc.n_sims.toLocaleString()} simulations · spot ${cur()}${mc.spot} · daily σ ${mc.daily_vol_pct}%
        </div>
        <div class="mc-pctl-grid">
            ${[['5th', p.p5, 'var(--red)'], ['25th', p.p25, 'var(--amber)'], ['50th', p.p50, 'var(--text-primary)'], ['75th', p.p75, 'var(--amber)'], ['95th', p.p95, 'var(--green)']]
                .map(([lbl, v, c]) => `<div class="mc-pctl"><div class="p">${lbl}</div><div class="pv" style="color:${c}">${cur()}${v != null ? v.toFixed(0) : '--'}</div></div>`).join('')}
        </div>
    `;

    // Histogram with 1-sigma band highlighted
    const hist = mc.histogram || {};
    const band = mc.expected_band || {};
    if (hist.counts && hist.counts.length) {
        const maxC = Math.max(...hist.counts);
        html += `<div class="mc-hist">`;
        hist.counts.forEach((c, i) => {
            const edgeLow = hist.edges[i], edgeHigh = hist.edges[i + 1];
            const inBand = edgeHigh >= band.low && edgeLow <= band.high;
            const h = maxC > 0 ? (c / maxC * 100) : 0;
            html += `<div class="mc-hist-bar ${inBand ? 'in-band' : ''}" style="height:${h}%" title="${cur()}${edgeLow.toFixed(0)}–${cur()}${edgeHigh.toFixed(0)}"></div>`;
        });
        html += `</div>`;
        html += `<div class="mc-band-labels"><span>${cur()}${hist.edges[0].toFixed(0)}</span><span style="color:var(--gold-light)">1σ band ${cur()}${band.low}–${cur()}${band.high}</span><span>${cur()}${hist.edges[hist.edges.length - 1].toFixed(0)}</span></div>`;
    }

    // Target probabilities
    if (mc.target_probabilities) {
        html += `<table class="indicator-table" style="margin-top:10px;"><thead><tr><th>Move</th><th>↑ Level</th><th>P(≥)</th><th>↓ Level</th><th>P(≤)</th></tr></thead><tbody>`;
        mc.target_probabilities.forEach(t => {
            html += `<tr>
                <td>±${t.move_pct}%</td>
                <td class="text-green">${cur()}${t.up_level.toFixed(0)}</td>
                <td>${t.prob_up_close}%</td>
                <td class="text-red">${cur()}${t.dn_level.toFixed(0)}</td>
                <td>${t.prob_dn_close}%</td>
            </tr>`;
        });
        html += `</tbody></table>`;
    }

    container.innerHTML = html;
}

// ═══════════════════════════════════════
// WORLD INDICES (global macro context)
// ═══════════════════════════════════════
// Inline SVG sparkline from a list of values. Colour comes from the parent
// .index-cell .up/.down class (CSS vars don't resolve in SVG attributes).
function sparkSvg(vals) {
    if (!vals || vals.length < 2) return '<div class="spark-empty"></div>';
    const w = 100, h = 30, pad = 3;
    const min = Math.min(...vals), max = Math.max(...vals), rng = (max - min) || 1;
    const xy = (v, i) => `${((i / (vals.length - 1)) * w).toFixed(1)},${(pad + (h - 2 * pad) - ((v - min) / rng) * (h - 2 * pad)).toFixed(1)}`;
    const line = vals.map(xy).join(' ');
    const area = `0,${h} ${line} ${w},${h}`;
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
        <polygon class="spark-fill" points="${area}"/>
        <polyline class="spark-line" points="${line}"/>
    </svg>`;
}

function renderWorldIndices() {
    const el = document.getElementById('world-indices');
    if (!el) return;
    const idx = (DATA && DATA.world_indices) || [];
    if (!idx.length) {
        el.innerHTML = '<div class="text-muted" style="font-size:0.72rem;">World index data unavailable.</div>';
        return;
    }
    el.innerHTML = idx.map(i => {
        const c = i.change_pct;
        const dir = c == null ? 'flat' : c > 0.001 ? 'up' : c < -0.001 ? 'down' : 'flat';
        const arrow = c == null ? '' : c > 0 ? '▲' : c < 0 ? '▼' : '–';
        const priceStr = i.price != null ? Number(i.price).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '--';
        const chgStr = c != null ? `${c >= 0 ? '+' : ''}${c.toFixed(2)}%` : '--';
        return `
            <div class="index-cell ${dir}">
                <div class="index-head">
                    <span class="index-name" title="${i.name} (${i.symbol})">${i.name}</span>
                    <span class="index-region">${i.region}</span>
                </div>
                <div class="index-spark">${sparkSvg(i.spark)}</div>
                <div class="index-foot">
                    <span class="index-price">${priceStr}</span>
                    <span class="index-chg">${arrow} ${chgStr}</span>
                </div>
            </div>`;
    }).join('');
}

// ═══════════════════════════════════════
// CONFLUENCE ZONES
// ═══════════════════════════════════════
function renderConfluence() {
    const zones = DATA.structure?.confluence_zones || [];
    const container = document.getElementById('confluence-zones');

    if (!zones.length) {
        container.innerHTML = '<div class="text-muted">No confluence zones detected near current price.</div>';
        return;
    }

    container.innerHTML = zones.map(z => {
        const dots = Array(Math.min(z.strength, 6)).fill('<span class="zone-dot"></span>').join('');
        const distColor = z.dist_pct > 0 ? 'var(--red)' : 'var(--green)';
        return `
            <div class="zone-item ${z.side}">
                <div class="zone-head">
                    <span class="zone-price">${cur()}${z.center.toFixed(2)}</span>
                    <span class="zone-strength" title="${z.strength} overlapping levels">${dots}</span>
                </div>
                <div class="zone-head">
                    <span class="zone-dist" style="color:${distColor}">${z.dist_pct >= 0 ? '+' : ''}${z.dist_pct}% · ${z.side}</span>
                    <span class="zone-dist">${cur()}${z.low.toFixed(0)}–${cur()}${z.high.toFixed(0)}</span>
                </div>
                <div class="zone-sources">${z.sources.join(' · ')}</div>
            </div>
        `;
    }).join('');
}

// ═══════════════════════════════════════
// STRUCTURE (ADX / VWAP / patterns / G:S ratio)
// ═══════════════════════════════════════
function renderStructure() {
    const s = DATA.structure || {};
    const container = document.getElementById('structure-content');
    const badge = document.getElementById('adx-badge');

    const adx = s.adx || {};
    if (adx.adx != null) {
        badge.textContent = `ADX ${adx.adx} · ${adx.direction}`;
        badge.style.color = adx.direction === 'Bullish' ? 'var(--green)' : 'var(--red)';
        badge.style.background = adx.direction === 'Bullish' ? 'var(--green-bg)' : 'var(--red-bg)';
    } else { badge.textContent = '--'; }

    let html = '';

    // Swing structure
    const sw = s.swing_structure || {};
    if (sw.label) {
        const c = sw.bias === 'Bullish' ? 'var(--green)' : sw.bias === 'Bearish' ? 'var(--red)' : 'var(--amber)';
        const bg = sw.bias === 'Bullish' ? 'var(--green-bg)' : sw.bias === 'Bearish' ? 'var(--red-bg)' : 'var(--amber-bg)';
        html += `
            <div style="padding:8px 10px; background:${bg}; border-radius:var(--radius-xs); border-left:3px solid ${c}; margin-bottom:10px;">
                <div style="font-size:0.75rem; font-weight:600; color:${c};">${sw.label}</div>
                <div style="font-size:0.62rem; color:var(--text-muted); margin-top:2px;">Swing range ${cur()}${sw.recent_low?.toFixed(0)}–${cur()}${sw.recent_high?.toFixed(0)} · price at ${sw.range_position_pct}% of range</div>
                <div style="margin-top:5px; height:6px; background:var(--bg-elevated); border-radius:3px; overflow:hidden;">
                    <div style="height:100%; width:${sw.range_position_pct}%; background:${c};"></div>
                </div>
            </div>`;
    }

    if (adx.adx != null) {
        html += `
            <div class="metric-row"><span class="k">Trend Strength (ADX)</span><span class="v">${adx.adx} — ${adx.strength}</span></div>
            <div class="metric-row"><span class="k">+DI / −DI</span><span class="v"><span class="text-green">${adx.plus_di}</span> / <span class="text-red">${adx.minus_di}</span></span></div>
        `;
    }

    const vwap = s.vwap || {};
    if (vwap.vwap != null) {
        const c = vwap.position.includes('Above') ? 'var(--green)' : 'var(--red)';
        html += `<div class="metric-row"><span class="k">VWAP (intraday)</span><span class="v">${cur()}${vwap.vwap.toFixed(2)} <span style="color:${c}; font-size:0.62rem;">(${vwap.dist_pct >= 0 ? '+' : ''}${vwap.dist_pct}%)</span></span></div>`;
    }

    const gsr = s.gold_silver_ratio || {};
    if (gsr.ratio != null) {
        html += `<div class="metric-row"><span class="k">Gold/Silver Ratio</span><span class="v">${gsr.ratio}</span></div>
                 <div style="font-size:0.62rem; color:var(--text-muted); margin:2px 0 8px;">${gsr.regime}</div>`;
    }

    // Patterns
    const patterns = s.patterns || [];
    if (patterns.length) {
        html += `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin:8px 0 4px;">Candlestick Patterns</div>`;
        html += patterns.map(p => {
            const c = p.bias === 'Bullish' ? 'var(--green)' : p.bias === 'Bearish' ? 'var(--red)' : 'var(--amber)';
            const bg = p.bias === 'Bullish' ? 'var(--green-bg)' : p.bias === 'Bearish' ? 'var(--red-bg)' : 'var(--amber-bg)';
            return `<div class="pattern-item">
                <span class="pattern-tag" style="color:${c}; background:${bg}">${p.bias}</span>
                <span><strong style="color:var(--text-primary)">${p.name}</strong><br><span style="color:var(--text-muted)">${p.note}</span></span>
            </div>`;
        }).join('');
    }

    container.innerHTML = html || '<div class="text-muted">No structure data</div>';
}

// ═══════════════════════════════════════
// SEASONALITY
// ═══════════════════════════════════════
function renderSeasonality() {
    const s = DATA.seasonality || {};
    const container = document.getElementById('seasonality-months');
    const badge = document.getElementById('season-badge');
    const summaryEl = document.getElementById('seasonality-summary');

    const months = s.monthly || [];
    if (!months.length) {
        badge.textContent = 'N/A';
        summaryEl.innerHTML = '<div class="text-muted">Insufficient history for seasonality.</div>';
        container.innerHTML = '';
        return;
    }

    const cm = s.current_month || {};
    badge.textContent = cm.month ? `${cm.month} ${cm.avg_return_pct >= 0 ? '+' : ''}${cm.avg_return_pct}%` : '--';
    const sc = s.seasonal_score || 0;
    badge.style.color = sc > 0 ? 'var(--green)' : sc < 0 ? 'var(--red)' : 'var(--amber)';
    badge.style.background = sc > 0 ? 'var(--green-bg)' : sc < 0 ? 'var(--red-bg)' : 'var(--amber-bg)';

    summaryEl.innerHTML = `<div style="font-size:0.72rem; color:var(--text-secondary);">${s.summary}</div>
        <div style="font-size:0.6rem; color:var(--text-muted); margin-top:2px;">Based on ${s.years_of_data} years of history</div>`;

    const maxAbs = Math.max(...months.map(m => Math.abs(m.avg_return_pct)), 0.5);
    let bars = `<div class="season-grid">`;
    months.forEach(m => {
        const h = Math.abs(m.avg_return_pct) / maxAbs * 100;
        const isCur = cm.month_num === m.month_num;
        bars += `<div class="season-col" title="${m.month}: ${m.avg_return_pct >= 0 ? '+' : ''}${m.avg_return_pct}% avg, ${m.win_rate}% win">
            <div class="season-bar ${m.avg_return_pct >= 0 ? 'pos' : 'neg'} ${isCur ? 'current' : ''}" style="height:${Math.max(h, 3)}%"></div>
            <span class="season-mlabel">${m.month[0]}</span>
        </div>`;
    });
    bars += `</div><div style="font-size:0.58rem; color:var(--text-muted); text-align:center;">Avg monthly return by calendar month (green=positive)</div>`;
    container.innerHTML = bars;

    // Day of week
    const dowEl = document.getElementById('seasonality-dow');
    const dows = s.day_of_week || [];
    const curDow = (s.current_dow || {}).dow_num;
    let dowHtml = '';
    if (dows.length) {
        dowHtml += `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">Avg return by weekday</div>`;
        dowHtml += `<div class="dow-grid">${dows.map(d => `
            <div class="dow-cell ${d.dow_num === curDow ? 'current' : ''}">
                <div class="d">${d.day}</div>
                <div class="r" style="color:${d.avg_return_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${d.avg_return_pct >= 0 ? '+' : ''}${d.avg_return_pct}%</div>
            </div>`).join('')}</div>`;
    }

    // Quarterly strip
    const qs = s.quarterly || [];
    const curQ = (s.current_quarter || {}).quarter_num;
    if (qs.length) {
        dowHtml += `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin:10px 0 4px;">Quarterly seasonality</div>`;
        dowHtml += `<div class="dow-grid">${qs.map(q => `
            <div class="dow-cell ${q.quarter_num === curQ ? 'current' : ''}">
                <div class="d">${q.quarter}</div>
                <div class="r" style="color:${q.avg_return_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${q.avg_return_pct >= 0 ? '+' : ''}${q.avg_return_pct}%</div>
                <div style="font-size:0.55rem; color:var(--text-muted)">${q.win_rate}% win</div>
            </div>`).join('')}</div>`;
    }

    // Best / worst months
    const best = s.best_months || [], worst = s.worst_months || [];
    if (best.length && worst.length) {
        const chip = (m, up) => `<span style="display:inline-block; font-size:0.62rem; padding:2px 7px; margin:2px; border-radius:10px; background:${up ? 'var(--green-bg)' : 'var(--red-bg)'}; color:${up ? 'var(--green)' : 'var(--red)'};">${m.month} ${m.avg_return_pct >= 0 ? '+' : ''}${m.avg_return_pct}%</span>`;
        dowHtml += `<div style="margin-top:10px; font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:2px;">Strongest months</div>
            <div>${best.map(m => chip(m, true)).join('')}</div>
            <div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin:6px 0 2px;">Weakest months</div>
            <div>${worst.map(m => chip(m, false)).join('')}</div>`;
    }

    dowEl.innerHTML = dowHtml;
}

// ═══════════════════════════════════════
// BACKTEST
// ═══════════════════════════════════════
function renderBacktest() {
    const bt = DATA.backtest || {};
    const stratEl = document.getElementById('backtest-strategy');
    const rulesEl = document.getElementById('backtest-rules');
    const badge = document.getElementById('bt-badge');

    if (!bt.available) {
        badge.textContent = 'N/A';
        stratEl.innerHTML = '<div class="text-muted">Backtest unavailable</div>';
        return;
    }
    badge.textContent = `${bt.horizon_days}d forward`;

    const st = bt.strategy || {};
    if (st.strategy) {
        const s = st.strategy, b = st.buy_hold || {};
        stratEl.innerHTML = `
            <div style="font-size:0.65rem; color:var(--text-muted); margin-bottom:6px;">${st.description}</div>
            <div class="bt-compare">
                <div class="bt-col strat">
                    <h4>📈 Score Strategy</h4>
                    <div class="metric-row"><span class="k">Total</span><span class="v" style="color:${s.total_return_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${s.total_return_pct}%</span></div>
                    <div class="metric-row"><span class="k">Sharpe</span><span class="v">${s.sharpe}</span></div>
                    <div class="metric-row"><span class="k">Max DD</span><span class="v text-red">${s.max_drawdown_pct}%</span></div>
                    <div class="metric-row"><span class="k">In market</span><span class="v">${s.time_in_market_pct}%</span></div>
                </div>
                <div class="bt-col">
                    <h4>🪙 Buy & Hold</h4>
                    <div class="metric-row"><span class="k">Total</span><span class="v" style="color:${b.total_return_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${b.total_return_pct}%</span></div>
                    <div class="metric-row"><span class="k">Sharpe</span><span class="v">${b.sharpe}</span></div>
                    <div class="metric-row"><span class="k">Max DD</span><span class="v text-red">${b.max_drawdown_pct}%</span></div>
                    <div class="metric-row"><span class="k">Ann.</span><span class="v">${b.annual_return_pct}%</span></div>
                </div>
            </div>
        `;
        renderEquityCurve(st.equity_curve || []);
    }

    // Rule edges
    const rules = bt.rules || [];
    if (rules.length) {
        rulesEl.innerHTML = `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">Forward ${bt.horizon_days}d edge by rule (baseline ${bt.baseline.avg_return_pct}%)</div>
            <table class="indicator-table"><thead><tr><th>Rule</th><th>Avg</th><th>Win%</th><th>Edge</th><th>n</th></tr></thead><tbody>
            ${rules.map(r => `<tr>
                <td style="color:var(--text-secondary)">${r.rule}</td>
                <td style="color:${r.avg_return_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${r.avg_return_pct >= 0 ? '+' : ''}${r.avg_return_pct}%</td>
                <td>${r.win_rate}%</td>
                <td style="color:${r.edge_vs_baseline_pct >= 0 ? 'var(--green)' : 'var(--red)'}">${r.edge_vs_baseline_pct >= 0 ? '+' : ''}${r.edge_vs_baseline_pct}%</td>
                <td style="color:var(--text-muted)">${r.samples}</td>
            </tr>`).join('')}
            </tbody></table>`;
    }
}

function renderEquityCurve(curve) {
    const container = document.getElementById('equity-chart');
    container.innerHTML = '';
    if (!curve.length || typeof LightweightCharts === 'undefined') return;

    const etc = themeColors();
    const c = LightweightCharts.createChart(container, {
        width: container.clientWidth, height: 160,
        layout: { background: { type: 'solid', color: etc.bg }, textColor: etc.text, fontSize: 10 },
        grid: { vertLines: { color: etc.grid }, horzLines: { color: etc.grid } },
        timeScale: { borderColor: etc.border, timeVisible: false },
        rightPriceScale: { borderColor: etc.border },
        handleScroll: false, handleScale: false,
    });
    const strat = c.addLineSeries({ color: '#4CC2FF', lineWidth: 2, title: 'Strategy' });
    const bh = c.addLineSeries({ color: '#8B8B8E', lineWidth: 1, lineStyle: 2, title: 'Buy&Hold' });
    strat.setData(curve.map(p => ({ time: p.t, value: p.strat })));
    bh.setData(curve.map(p => ({ time: p.t, value: p.bh })));
    c.timeScale().fitContent();
    new ResizeObserver(() => c.applyOptions({ width: container.clientWidth })).observe(container);
}

// ═══════════════════════════════════════
// EVENT RISK + CHECKLIST
// ═══════════════════════════════════════
function renderEvents() {
    const sc = DATA.scenario || {};
    const calEl = document.getElementById('event-calendar');
    const checkEl = document.getElementById('risk-checklist');

    const events = sc.events || [];
    calEl.innerHTML = `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:5px;">Upcoming High-Impact Events</div>` +
        events.map(e => {
            const impactCls = 'impact-' + (e.impact || '').toLowerCase().replace(/\s/g, '');
            return `<div class="event-item ${e.imminent ? 'imminent' : ''}">
                <span class="event-days">${e.days_until}d</span>
                <span class="event-name">${e.event}<br><span class="event-note">${e.date_label} · ${e.note}</span></span>
                <span class="event-impact ${impactCls}">${e.impact}</span>
            </div>`;
        }).join('');

    const checks = sc.checklist || [];
    checkEl.innerHTML = `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin:8px 0 5px;">Pre-Session Checklist</div>` +
        checks.map(c => `<div class="check-item check-${c.status}">
            <span class="check-icon">${c.status === 'ok' ? '✓' : '⚠'}</span>
            <span>${c.text}</span></div>`).join('');
}

// ═══════════════════════════════════════
// SCENARIOS + GOLD IN FX
// ═══════════════════════════════════════
function renderScenarios() {
    const sc = DATA.scenario || {};
    const fxEl = document.getElementById('gold-in-fx');
    const scenEl = document.getElementById('macro-scenarios');

    // FX conversion assumes a USD-quoted price — skip for non-USD assets (₹ stocks).
    const fx = (cur() === '$') ? (sc.gold_in_fx || []) : [];
    fxEl.innerHTML = '';
    if (fx.length) {
        fxEl.innerHTML = `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:5px;">${metal()} Priced In</div>
            <div class="fx-grid">${fx.map(f => `
                <div class="fx-cell"><div class="fx-cur">${f.currency}</div>
                <div class="fx-val">${f.symbol}${Number(f.price).toLocaleString()}</div></div>`).join('')}</div>`;
    }

    const sens = sc.sensitivities || {};
    const scenarios = sens.scenarios || [];
    if (scenarios.length) {
        let html = `<div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase; margin:4px 0 5px;">Macro Sensitivity (last 60d betas)</div>`;
        html += scenarios.map(s => {
            const c = s.gold_pct >= 0 ? 'var(--green)' : 'var(--red)';
            return `<div class="scenario-item">
                <span class="scenario-driver">${s.driver}</span>
                <span class="scenario-impact" style="color:${c}">${s.gold_pct >= 0 ? '+' : ''}${s.gold_pct}%${s.gold_price ? ' → $' + s.gold_price.toFixed(0) : ''}</span>
            </div>`;
        }).join('');
        if (sens.dxy_beta != null) {
            html += `<div style="font-size:0.6rem; color:var(--text-muted); margin-top:4px;">DXY β: ${sens.dxy_beta} · 10Y yield β: ${sens.yield_beta ?? 'N/A'}</div>`;
        }
        scenEl.innerHTML = html;
    }
}

// ═══════════════════════════════════════
// TOOLBAR (refresh / export / auto)
// ═══════════════════════════════════════
let autoRefreshTimer = null;
function setupToolbar() {
    const refreshBtn = document.getElementById('refresh-btn');
    const printBtn = document.getElementById('print-btn');
    const autoToggle = document.getElementById('autorefresh-toggle');

    if (refreshBtn) refreshBtn.onclick = () => loadData();
    if (printBtn) printBtn.onclick = () => window.print();
    const themeBtn = document.getElementById('theme-btn');
    if (themeBtn) themeBtn.onclick = toggleTheme;
    if (autoToggle) {
        autoToggle.onchange = () => {
            if (autoToggle.checked) {
                autoRefreshTimer = setInterval(loadData, 60000);
            } else {
                clearInterval(autoRefreshTimer);
            }
        };
    }
}

// ═══════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════
function getSignalColor(signal) {
    if (!signal) return 'var(--text-muted)';
    const s = signal.toLowerCase();
    if (s.includes('bullish') || s.includes('overbought') || s === 'high volume') return 'var(--green)';
    if (s.includes('bearish') || s.includes('oversold')) return 'var(--red)';
    return 'var(--amber)';
}

// ── Initialize ──
document.addEventListener('DOMContentLoaded', () => { initTheme(); loadData(); });
