/**
 * ═══════════════════════════════════════════════════════════════
 *  Gold Pre-Session Dashboard — Interactive Frontend
 *  Renders all analysis data from session_data.json
 * ═══════════════════════════════════════════════════════════════
 */

let DATA = null;
let chart = null;
let candleSeries = null;

// ── Load Data ──
async function loadData() {
    try {
        const response = await fetch('session_data.json?t=' + Date.now());
        DATA = await response.json();
        document.getElementById('loading').style.display = 'none';
        document.getElementById('dashboard').style.display = 'block';
        renderAll();
    } catch (error) {
        document.querySelector('.loading-text').textContent = 
            'Error loading data. Make sure run_session.py has been executed.';
        console.error('Failed to load session data:', error);
    }
}

// ── Render All Sections ──
function renderAll() {
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
    setupChartTabs();
    setupPivotTabs();
}

// ═══════════════════════════════════════
// HEADER
// ═══════════════════════════════════════
function renderHeader() {
    const tech = DATA.technical;
    const session = DATA.session_plan;
    
    // Price
    const price = tech.current_price;
    document.getElementById('hero-price').textContent = price ? `$${price.toFixed(2)}` : '$---';
    
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
    
    // Regime
    document.getElementById('signal-regime').textContent = sig.regime || '--';
    
    // Breakdown
    const breakdownEl = document.getElementById('signal-breakdown');
    breakdownEl.innerHTML = '';
    
    if (sig.breakdown) {
        const items = ['technical', 'macro', 'sentiment', 'volatility', 'correlation'];
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
    const container = document.getElementById('price-chart');
    container.innerHTML = '';
    
    const candles = DATA.technical.candlestick_data?.[timeframe];
    if (!candles || candles.length === 0) {
        container.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:60px;">No chart data available</div>';
        return;
    }
    
    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 400,
        layout: {
            background: { type: 'solid', color: '#111113' },
            textColor: '#8B8B8E',
            fontSize: 11,
            fontFamily: 'Inter, sans-serif',
        },
        grid: {
            vertLines: { color: 'rgba(255,255,255,0.03)' },
            horzLines: { color: 'rgba(255,255,255,0.03)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: { color: 'rgba(91, 91, 214, 0.15)', labelBackgroundColor: '#5B5BD6' },
            horzLine: { color: 'rgba(91, 91, 214, 0.15)', labelBackgroundColor: '#5B5BD6' },
        },
        timeScale: {
            borderColor: 'rgba(255,255,255,0.06)',
            timeVisible: timeframe === '1h',
        },
        rightPriceScale: {
            borderColor: 'rgba(255,255,255,0.06)',
        },
    });
    
    candleSeries = chart.addCandlestickSeries({
        upColor: '#45A557',
        downColor: '#E5484D',
        borderUpColor: '#45A557',
        borderDownColor: '#E5484D',
        wickUpColor: '#45A557',
        wickDownColor: '#E5484D',
    });
    
    candleSeries.setData(candles);
    
    // Add key level markers
    addChartLevels(timeframe);
    
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
                price: sma20, color: '#5B5BD6', lineWidth: 1, lineStyle: 2,
                title: 'SMA 20', axisLabelVisible: false,
            });
        }
        if (sma50) {
            const line2 = candleSeries.createPriceLine({
                price: sma50, color: '#7C66DC', lineWidth: 1, lineStyle: 2,
                title: 'SMA 50', axisLabelVisible: false,
            });
        }
    }
    
    // Pivot point
    if (pivots.PP) {
        candleSeries.createPriceLine({
            price: pivots.PP, color: '#5B5BD6', lineWidth: 1, lineStyle: 0,
            title: 'PP', axisLabelVisible: true,
        });
    }
    if (pivots.R1) {
        candleSeries.createPriceLine({
            price: pivots.R1, color: '#E5484D', lineWidth: 1, lineStyle: 2,
            title: 'R1', axisLabelVisible: true,
        });
    }
    if (pivots.S1) {
        candleSeries.createPriceLine({
            price: pivots.S1, color: '#45A557', lineWidth: 1, lineStyle: 2,
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
                $${item.value?.toFixed(2) || '--'}
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
            <span class="level-value text-gold">$${item.value?.toFixed(2) || '--'}</span>
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
            <div style="font-size:0.65rem; color:var(--text-muted); margin-left:112px; margin-bottom:8px;">${ns.article_count || 0} gold-related articles analyzed</div>
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
            <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">Gold-Related Headlines</div>
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
                    <span class="text-green font-mono" style="font-size:0.85rem;">$${range.expected_low?.toFixed(2)}</span>
                    <span class="text-gold font-mono font-bold" style="font-size:0.85rem;">$${range.atr_14?.toFixed(2)}</span>
                    <span class="text-red font-mono" style="font-size:0.85rem;">$${range.expected_high?.toFixed(2)}</span>
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
                    ${item.isSignal ? item.value : '$' + item.value?.toFixed(2)}
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
                <span class="level-value ${color}">$${val.toFixed(2)}</span>
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
    
    // MCX Gold equivalent
    if (mcx.mcx_gold_equivalent) {
        html += `
            <div class="mcx-highlight">
                <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">MCX Gold Equivalent (per 10g)</div>
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
    
    // GOLDBEES
    if (mcx.goldbees_price) {
        html += `
            <div class="risk-item" style="flex:1;">
                <div class="label">GOLDBEES</div>
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
    
    if (setups.length === 0) {
        container.innerHTML = '<div class="text-muted">No trade setups generated. Signal may be too weak for high-conviction entries.</div>';
        return;
    }
    
    container.innerHTML = setups.map(setup => {
        const type = (setup.type || 'range').toLowerCase();
        
        let levelsHtml = '';
        if (setup.entry != null) {
            levelsHtml = `
                <div class="trade-levels">
                    <div class="trade-level">
                        <div class="label">Entry</div>
                        <div class="price text-gold">$${setup.entry?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Stop Loss</div>
                        <div class="price text-red">$${setup.stop_loss?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Target 1</div>
                        <div class="price text-green">$${setup.target_1?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Target 2</div>
                        <div class="price text-green">$${setup.target_2?.toFixed(2)}</div>
                    </div>
                </div>
            `;
        } else if (setup.buy_zone != null) {
            levelsHtml = `
                <div class="trade-levels">
                    <div class="trade-level">
                        <div class="label">Buy Zone</div>
                        <div class="price text-green">$${setup.buy_zone?.toFixed(2)}</div>
                    </div>
                    <div class="trade-level">
                        <div class="label">Sell Zone</div>
                        <div class="price text-red">$${setup.sell_zone?.toFixed(2)}</div>
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
                <div class="value text-gold">$${risk.atr_14?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">Tight Stop (0.5 ATR)</div>
                <div class="value text-red">$${risk.stop_tight?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">Normal Stop (1 ATR)</div>
                <div class="value text-red">$${risk.stop_normal?.toFixed(2) || '--'}</div>
            </div>
        </div>
    `;
    
    // Targets
    html += `
        <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px;">Target Distances</div>
        <div class="risk-grid" style="margin-bottom:14px;">
            <div class="risk-item">
                <div class="label">1R Target</div>
                <div class="value text-green">$${risk.target_1r?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">2R Target</div>
                <div class="value text-green">$${risk.target_2r?.toFixed(2) || '--'}</div>
            </div>
            <div class="risk-item">
                <div class="label">3R Target</div>
                <div class="value text-green">$${risk.target_3r?.toFixed(2) || '--'}</div>
            </div>
        </div>
    `;
    
    // Position sizing for account sizes
    const sizes = [10000, 50000, 100000];
    html += `<div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px;">Position Sizing (1% Risk)</div>`;
    
    html += '<table class="indicator-table"><thead><tr><th>Account</th><th>Risk/Trade</th><th>Micro Gold</th><th>Standard</th></tr></thead><tbody>';
    
    sizes.forEach(size => {
        const s = risk[`sizing_${size}`];
        if (!s) return;
        html += `
            <tr>
                <td>$${(size/1000)}K</td>
                <td>$${s.risk_per_trade_1pct?.toFixed(0)}</td>
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
                <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">🇮🇳 MCX Gold</div>
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
document.addEventListener('DOMContentLoaded', loadData);
