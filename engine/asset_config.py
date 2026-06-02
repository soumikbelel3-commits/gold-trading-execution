"""
╔══════════════════════════════════════════════════════════════════╗
║         Pre-Session — Asset Configuration                        ║
║   Parameterizes the (otherwise asset-agnostic) engines so the    ║
║   same pipeline can run for Gold or Silver.                      ║
╚══════════════════════════════════════════════════════════════════╝

Each engine takes plain DataFrames/dicts, so only a handful of things are
truly metal-specific: the price ticker, the "other metal" used for the
gold/silver ratio, the India/MCX contract specifics, the COMEX futures
point values used for position sizing, and a few display labels. They all
live here.
"""

ASSETS = {
    "gold": {
        "key": "gold",
        "name": "Gold",
        "symbol": "XAU/USD",
        "logo": "Au",
        "asset_class": "metal",
        "ticker": "GC=F",
        "etf": "GLD",
        # Counter-metal used for the gold/silver ratio + correlation panel.
        "other_metal": {"key": "Silver", "ticker": "SI=F"},
        # India / MCX
        "mcx": {
            "name": "MCX Gold",
            "proxy_ticker": "GOLDBEES.NS",
            "proxy_label": "GOLDBEES",
            "unit_label": "10g",
            "unit_grams": 10,            # rupee quote is per 10 grams
            "session_times": "09:00 AM - 11:30 PM IST",
            "contract": "MCX Gold (1 kg) / Gold Mini (100g) / Gold Petal (1g)",
            "lot_label": "100g (Gold Mini)",
            "tick_value": "Rs.100",
            "key_factors": [
                "RBI policy stance and USDINR intervention",
                "Physical gold demand (wedding/festival season)",
                "Import duty changes (currently ~15%)",
                "Sovereign Gold Bond issuance calendar",
            ],
        },
        # COMEX futures: $ P&L per $1.00 move in price.
        "futures": {
            "micro_label": "Micro Gold",
            "micro_point_value": 10,      # Micro Gold = 10 troy oz
            "standard_point_value": 100,  # Standard = 100 troy oz
        },
        "output_file": "session_data.json",
    },
    "silver": {
        "key": "silver",
        "name": "Silver",
        "symbol": "XAG/USD",
        "logo": "Ag",
        "asset_class": "metal",
        "ticker": "SI=F",
        "etf": "SLV",
        "other_metal": {"key": "Gold", "ticker": "GC=F"},
        "mcx": {
            "name": "MCX Silver",
            "proxy_ticker": "SILVERBEES.NS",
            "proxy_label": "SILVERBEES",
            "unit_label": "kg",
            "unit_grams": 1000,           # rupee quote is per kilogram
            "session_times": "09:00 AM - 11:30 PM IST",
            "contract": "MCX Silver (30 kg) / Silver Mini (5 kg) / Silver Micro (1 kg)",
            "lot_label": "5 kg (Silver Mini)",
            "tick_value": "Rs.5",
            "key_factors": [
                "Industrial demand (solar, EV, electronics)",
                "Gold/Silver ratio extremes (relative value)",
                "USDINR moves and import duty (~15%)",
                "Higher beta than gold - larger intraday swings",
            ],
        },
        # COMEX futures: $ P&L per $1.00 move in price.
        "futures": {
            "micro_label": "Micro Silver",
            "micro_point_value": 1000,    # Micro Silver = 1,000 troy oz
            "standard_point_value": 5000, # Standard = 5,000 troy oz
        },
        "output_file": "session_data_silver.json",
    },
}


# ── Crypto assets ──────────────────────────────────────────────────
# A different asset class: no MCX/India contract, no gold-silver ratio,
# trades 24/7, and risk-on rather than safe-haven. The metals-specific
# panels are hidden in the dashboard; macro is relabeled honestly (VIX
# treated as a risk-off headwind, not a safe-haven bid). `peer` is the
# comparison crypto added to the cross-asset universe. Sizing is in spot
# units of the coin (point value = $1 per $1 move per coin).
def _crypto(key, name, symbol, logo, ticker, peer):
    return {
        "key": key,
        "name": name,
        "symbol": symbol,
        "logo": logo,
        "asset_class": "crypto",
        "ticker": ticker,
        "peer": peer,  # {"key","ticker"} other major crypto for correlations
        "futures": {
            "micro_label": f"{symbol.split('/')[0]} units",
            "micro_point_value": 1,      # spot: 1 coin, $1 P&L per $1 move
            "standard_point_value": 1,
        },
        "output_file": f"session_data_{key}.json",
    }


ASSETS.update({
    "bitcoin":  _crypto("bitcoin",  "Bitcoin",  "BTC/USD", "₿", "BTC-USD", {"key": "ETH", "ticker": "ETH-USD"}),
    "ethereum": _crypto("ethereum", "Ethereum", "ETH/USD", "Ξ", "ETH-USD", {"key": "BTC", "ticker": "BTC-USD"}),
    "solana":   _crypto("solana",   "Solana",   "SOL/USD", "◎", "SOL-USD", {"key": "BTC", "ticker": "BTC-USD"}),
    "bnb":      _crypto("bnb",       "BNB",      "BNB/USD", "⬡", "BNB-USD", {"key": "BTC", "ticker": "BTC-USD"}),
    "xrp":      _crypto("xrp",       "XRP",      "XRP/USD", "✕", "XRP-USD", {"key": "BTC", "ticker": "BTC-USD"}),
})


# ── Equity index assets ────────────────────────────────────────────
# Risk-on asset class like crypto (no MCX, no gold/silver ratio, macro VIX
# treated as risk-off). Sized in index-futures points. `peer` is the other
# index used for the correlation panel.
def _index(key, name, symbol, logo, ticker, peer, micro_label, micro_pv, std_pv):
    return {
        "key": key,
        "name": name,
        "symbol": symbol,
        "logo": logo,
        "asset_class": "index",
        "ticker": ticker,
        "peer": peer,
        "futures": {
            "micro_label": micro_label,
            "micro_point_value": micro_pv,    # $ P&L per 1.0 index point (micro)
            "standard_point_value": std_pv,   # $ P&L per 1.0 index point (e-mini)
        },
        "output_file": f"session_data_{key}.json",
    }


ASSETS.update({
    "sp500":  _index("sp500",  "S&P 500",    "SPX", "SPX", "^GSPC",
                     {"key": "Nasdaq", "ticker": "^IXIC"}, "Micro S&P (MES)", 5, 50),
    "nasdaq": _index("nasdaq", "Nasdaq 100", "NDX", "NDX", "^NDX",
                     {"key": "S&P500", "ticker": "^GSPC"}, "Micro Nasdaq (MNQ)", 2, 20),
})

# Order in which assets appear in the dashboard toggle / pipeline runs.
ASSET_ORDER = ["gold", "silver", "bitcoin", "ethereum", "solana", "bnb", "xrp",
               "sp500", "nasdaq"]

DEFAULT_ASSET = "gold"
