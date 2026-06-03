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


# ── Non-precious commodities ───────────────────────────────────────
# Cyclical/inflation commodities (energy, industrial metals). No MCX, no
# gold/silver ratio. Treated as risk-on for the VIX factor (risk-off = demand
# fear). USD-denominated. Sized in futures points ($ P&L per $1.00 move).
def _commodity(key, name, symbol, logo, ticker, peer, micro_label, micro_pv, std_pv):
    return {
        "key": key, "name": name, "symbol": symbol, "logo": logo,
        "asset_class": "commodity", "ticker": ticker, "peer": peer,
        "futures": {"micro_label": micro_label, "micro_point_value": micro_pv,
                    "standard_point_value": std_pv},
        "output_file": f"session_data_{key}.json",
    }


# ── Indian equities (Nifty large-caps) ─────────────────────────────
# Risk-on equities priced in INR. No MCX, no gold/silver ratio. NSE cash
# session. Sized in shares. Peer = Nifty 50 index.
def _stock(key, name, symbol, logo, ticker):
    return {
        "key": key, "name": name, "symbol": symbol, "logo": logo,
        "asset_class": "stock", "ticker": ticker, "currency": "Rs.",
        "peer": {"key": "Nifty50", "ticker": "^NSEI"},
        "futures": {"micro_label": "Shares", "micro_point_value": 1,
                    "standard_point_value": 1},
        "output_file": f"session_data_{key}.json",
    }


ASSETS.update({
    "crude":     _commodity("crude",     "Crude Oil (WTI)", "WTI",     "WTI", "CL=F", {"key": "Brent", "ticker": "BZ=F"}, "Micro WTI (MCL)", 100, 1000),
    "brent":     _commodity("brent",     "Brent Crude",     "BRENT",   "BRT", "BZ=F", {"key": "WTI", "ticker": "CL=F"},   "Brent (BZ)",      100, 1000),
    "natgas":    _commodity("natgas",    "Natural Gas",     "NATGAS",  "NG",  "NG=F", {"key": "WTI", "ticker": "CL=F"},   "Henry Hub (NG)",  2500, 10000),
    "copper":    _commodity("copper",    "Copper",          "COPPER",  "Cu",  "HG=F", {"key": "Gold", "ticker": "GC=F"},  "Copper (HG)",     2500, 25000),
    "platinum":  _commodity("platinum",  "Platinum",        "XPT/USD", "Pt",  "PL=F", {"key": "Gold", "ticker": "GC=F"},  "Platinum (PL)",   10, 50),
    "palladium": _commodity("palladium", "Palladium",       "XPD/USD", "Pd",  "PA=F", {"key": "Gold", "ticker": "GC=F"},  "Palladium (PA)",  10, 100),
})

ASSETS.update({
    "reliance":   _stock("reliance",   "Reliance",        "RELIANCE",   "REL",  "RELIANCE.NS"),
    "tcs":        _stock("tcs",        "TCS",             "TCS",        "TCS",  "TCS.NS"),
    "hdfcbank":   _stock("hdfcbank",   "HDFC Bank",       "HDFCBANK",   "HDFC", "HDFCBANK.NS"),
    "icicibank":  _stock("icicibank",  "ICICI Bank",      "ICICIBANK",  "ICICI","ICICIBANK.NS"),
    "infosys":    _stock("infosys",    "Infosys",         "INFY",       "INFY", "INFY.NS"),
    "hindunilvr": _stock("hindunilvr", "Hind. Unilever",  "HINDUNILVR", "HUL",  "HINDUNILVR.NS"),
    "itc":        _stock("itc",        "ITC",             "ITC",        "ITC",  "ITC.NS"),
    "sbin":       _stock("sbin",       "State Bank (SBI)","SBIN",       "SBI",  "SBIN.NS"),
    "bhartiartl": _stock("bhartiartl", "Bharti Airtel",   "BHARTIARTL", "BHRT", "BHARTIARTL.NS"),
    "kotakbank":  _stock("kotakbank",  "Kotak Bank",      "KOTAKBANK",  "KTK",  "KOTAKBANK.NS"),
    "lt":         _stock("lt",         "Larsen & Toubro", "LT",         "L&T",  "LT.NS"),
    "bajfinance": _stock("bajfinance", "Bajaj Finance",   "BAJFINANCE", "BAJ",  "BAJFINANCE.NS"),
    "axisbank":   _stock("axisbank",   "Axis Bank",       "AXISBANK",   "AXIS", "AXISBANK.NS"),
    "asianpaint": _stock("asianpaint", "Asian Paints",    "ASIANPAINT", "APNT", "ASIANPAINT.NS"),
    "maruti":     _stock("maruti",     "Maruti Suzuki",   "MARUTI",     "MRTI", "MARUTI.NS"),
    "sunpharma":  _stock("sunpharma",  "Sun Pharma",      "SUNPHARMA",  "SUN",  "SUNPHARMA.NS"),
    "titan":      _stock("titan",      "Titan",           "TITAN",      "TITN", "TITAN.NS"),
    "wipro":      _stock("wipro",      "Wipro",           "WIPRO",      "WIPR", "WIPRO.NS"),
    "ultracemco": _stock("ultracemco", "UltraTech Cement","ULTRACEMCO", "UTCL", "ULTRACEMCO.NS"),
    "nestleind":  _stock("nestleind",  "Nestle India",    "NESTLEIND",  "NEST", "NESTLEIND.NS"),
})

# Order in which assets appear in the dashboard toggle / pipeline runs.
ASSET_ORDER = (
    ["gold", "silver"]
    + ["crude", "brent", "natgas", "copper", "platinum", "palladium"]
    + ["bitcoin", "ethereum", "solana", "bnb", "xrp"]
    + ["sp500", "nasdaq"]
    + ["reliance", "tcs", "hdfcbank", "icicibank", "infosys", "hindunilvr",
       "itc", "sbin", "bhartiartl", "kotakbank", "lt", "bajfinance", "axisbank",
       "asianpaint", "maruti", "sunpharma", "titan", "wipro", "ultracemco", "nestleind"]
)

# Asset groups for the dashboard navbar dropdowns.
ASSET_GROUPS = [
    {"key": "commodity", "label": "Commodity",
     "assets": ["gold", "silver", "crude", "brent", "natgas", "copper", "platinum", "palladium"]},
    {"key": "crypto", "label": "Crypto",
     "assets": ["bitcoin", "ethereum", "solana", "bnb", "xrp"]},
    {"key": "index", "label": "Index",
     "assets": ["sp500", "nasdaq"]},
    {"key": "stock", "label": "Stock",
     "assets": ["reliance", "tcs", "hdfcbank", "icicibank", "infosys", "hindunilvr",
                "itc", "sbin", "bhartiartl", "kotakbank", "lt", "bajfinance", "axisbank",
                "asianpaint", "maruti", "sunpharma", "titan", "wipro", "ultracemco", "nestleind"]},
]

DEFAULT_ASSET = "gold"
