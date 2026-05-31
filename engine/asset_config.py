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

DEFAULT_ASSET = "gold"
