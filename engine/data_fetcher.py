"""
╔══════════════════════════════════════════════════════════════════╗
║           Gold Pre-Session — Data Fetcher                        ║
║   Live gold, cross-asset, and MCX data acquisition               ║
╚══════════════════════════════════════════════════════════════════╝
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
import json

try:
    from .asset_config import ASSETS, DEFAULT_ASSET
except ImportError:  # allow running as a top-level module
    from asset_config import ASSETS, DEFAULT_ASSET

warnings.filterwarnings("ignore")

# Major global equity indices for the World Indices overview panel.
# (display name, yfinance symbol, region)
WORLD_INDICES = [
    ("S&P 500", "^GSPC", "US"),
    ("Nasdaq", "^IXIC", "US"),
    ("Dow Jones", "^DJI", "US"),
    ("Russell 2000", "^RUT", "US"),
    ("FTSE 100", "^FTSE", "UK"),
    ("DAX", "^GDAXI", "DE"),
    ("CAC 40", "^FCHI", "FR"),
    ("Euro Stoxx 50", "^STOXX50E", "EU"),
    ("Nikkei 225", "^N225", "JP"),
    ("Hang Seng", "^HSI", "HK"),
    ("Nifty 50", "^NSEI", "IN"),
    ("Sensex", "^BSESN", "IN"),
    ("KOSPI", "^KS11", "KR"),
    ("ASX 200", "^AXJO", "AU"),
]

# Path to existing data collection pipeline
DATA_COLLECTION_DIR = Path(__file__).resolve().parent.parent.parent / "Data collection" / "data" / "raw"
SENTIMENT_DIR = DATA_COLLECTION_DIR.parent / "raw" / "sentiment_data"


class GoldDataFetcher:
    """
    Fetches precious-metal and cross-asset data from multiple sources.

    Primary: yfinance (live)
    Secondary: Existing parquet files from Data Collection pipeline

    `asset_key` ("gold" or "silver") selects the price ticker, MCX proxy and
    cross-asset universe via engine.asset_config. Defaults to gold for
    backward compatibility.
    """

    def __init__(self, asset_key: str = DEFAULT_ASSET):
        self.asset_key = asset_key
        self.asset_cfg = ASSETS.get(asset_key, ASSETS[DEFAULT_ASSET])
        self.ticker = self.asset_cfg["ticker"]

        self.end_date = datetime.now()
        self.start_1y = self.end_date - timedelta(days=365)
        self.start_6m = self.end_date - timedelta(days=180)
        self.start_3m = self.end_date - timedelta(days=90)
        self.start_1m = self.end_date - timedelta(days=30)

        # Cross-asset universe — depends on asset class.
        self.asset_class = self.asset_cfg.get("asset_class", "metal")
        if self.asset_class == "crypto":
            # Risk-on framing: equities (SPY/QQQ) and the peer crypto matter
            # most; gold is kept as a macro reference, VIX for risk sentiment.
            peer = self.asset_cfg.get("peer", {"key": "BTC", "ticker": "BTC-USD"})
            cross = {
                "DXY": "DX-Y.NYB",
                "US10Y": "^TNX",
                "US02Y": "^IRX",
                "SPY": "SPY",
                "QQQ": "QQQ",
                "Gold": "GC=F",
                "VIX": "^VIX",
            }
            # Add BTC and ETH as crypto references (excluding self).
            for k, t in (("BTC", "BTC-USD"), ("ETH", "ETH-USD")):
                if t != self.ticker:
                    cross[k] = t
            # Ensure the configured peer is present.
            cross.setdefault(peer["key"], peer["ticker"])
            self.cross_assets = cross
        elif self.asset_class == "index":
            # Equity index: compare against macro drivers + other indices.
            peer = self.asset_cfg.get("peer", {"key": "S&P500", "ticker": "^GSPC"})
            cross = {
                "DXY": "DX-Y.NYB",
                "US10Y": "^TNX",
                "US02Y": "^IRX",
                "VIX": "^VIX",
                "Gold": "GC=F",
                "DowJones": "^DJI",
                "BTC": "BTC-USD",
            }
            cross.setdefault(peer["key"], peer["ticker"])
            self.cross_assets = cross
        elif self.asset_class == "commodity":
            # Cyclical commodity: USD, growth (SPY), risk (VIX), and peer
            # commodities for context.
            peer = self.asset_cfg.get("peer", {"key": "Gold", "ticker": "GC=F"})
            cross = {
                "DXY": "DX-Y.NYB",
                "US10Y": "^TNX",
                "SPY": "SPY",
                "VIX": "^VIX",
                "Gold": "GC=F",
                "CrudeOil": "CL=F",
                "Copper": "HG=F",
            }
            cross.setdefault(peer["key"], peer["ticker"])
            self.cross_assets = cross
        elif self.asset_class == "stock":
            # Indian equity: Nifty/Sensex benchmarks, USDINR, US risk proxies.
            peer = self.asset_cfg.get("peer", {"key": "Nifty50", "ticker": "^NSEI"})
            cross = {
                "DXY": "DX-Y.NYB",
                "US10Y": "^TNX",
                "SPY": "SPY",
                "VIX": "^VIX",
                "Nifty50": "^NSEI",
                "Sensex": "^BSESN",
                "USDINR": "USDINR=X",
                "Gold": "GC=F",
            }
            cross.setdefault(peer["key"], peer["ticker"])
            self.cross_assets = cross
        else:
            # Metals: the "other metal" (silver for gold, gold for silver) is
            # included so the gold/silver ratio + correlation panel work.
            other = self.asset_cfg["other_metal"]
            self.cross_assets = {
                "DXY": "DX-Y.NYB",
                "US10Y": "^TNX",
                "US02Y": "^IRX",
                "SPY": "SPY",
                "TLT": "TLT",
                "CrudeOil": "CL=F",
                other["key"]: other["ticker"],
                "BTC": "BTC-USD",
                "VIX": "^VIX",
                f"{self.asset_cfg['etf']}_ETF": self.asset_cfg["etf"],
            }
    
    def fetch_gold_multi_timeframe(self) -> dict:
        """
        Fetch gold futures data at multiple timeframes.
        Returns dict with keys: '1h', '4h', 'daily'
        """
        result = {}
        
        # Daily — 1 year
        try:
            daily = yf.download(self.ticker, start=self.start_1y, end=self.end_date,
                               interval="1d", progress=False)
            if isinstance(daily.columns, pd.MultiIndex):
                daily.columns = daily.columns.get_level_values(0)
            result["daily"] = daily
        except Exception as e:
            print(f"  ⚠ Daily gold data error: {e}")
            result["daily"] = pd.DataFrame()
        
        # 1-Hour — 60 days (yfinance limit for 1h)
        try:
            h1 = yf.download(self.ticker, period="60d", interval="1h", progress=False)
            if isinstance(h1.columns, pd.MultiIndex):
                h1.columns = h1.columns.get_level_values(0)
            result["1h"] = h1
        except Exception as e:
            print(f"  ⚠ 1H gold data error: {e}")
            result["1h"] = pd.DataFrame()
        
        # 4-Hour approximation (resample 1h to 4h)
        if not result["1h"].empty:
            h4 = result["1h"].resample("4h").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum"
            }).dropna()
            result["4h"] = h4
        else:
            result["4h"] = pd.DataFrame()
        
        return result
    
    def fetch_gold_long_history(self) -> pd.DataFrame:
        """
        Fetch a long daily history of gold futures (max available) for
        machine-learning, seasonality, and backtesting modules that need
        many years of samples rather than a single year.
        """
        try:
            hist = yf.download(self.ticker, period="max", interval="1d", progress=False)
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            # Keep at most ~15 years to bound compute
            if len(hist) > 3800:
                hist = hist.tail(3800)
            return hist
        except Exception as e:
            print(f"  WARNING: Long-history gold data error: {e}")
            return pd.DataFrame()

    def fetch_chart_history(self) -> pd.DataFrame:
        """
        Full available daily history (UNCAPPED) for the long-range price chart.
        yfinance typically serves GC=F / SI=F from ~2000 onward (~25 years).
        Resampled to weekly candles downstream so the payload stays small.
        """
        try:
            hist = yf.download(self.ticker, period="max", interval="1d", progress=False)
            if isinstance(hist.columns, pd.MultiIndex):
                hist.columns = hist.columns.get_level_values(0)
            return hist
        except Exception as e:
            print(f"  WARNING: Chart history error: {e}")
            return pd.DataFrame()

    def fetch_fx_rates(self) -> dict:
        """
        Fetch FX rates used to express gold in non-USD currencies.
        Returns latest spot rates for EUR/USD, USD/JPY, and GBP/USD.
        (USD/INR is fetched separately within the MCX block.)
        """
        rates = {}
        fx_map = {"EURUSD": "EURUSD=X", "USDJPY": "USDJPY=X", "GBPUSD": "GBPUSD=X"}
        for name, ticker in fx_map.items():
            try:
                df = yf.download(ticker, period="5d", interval="1d", progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                rates[name] = float(df["Close"].iloc[-1]) if not df.empty else None
            except Exception:
                rates[name] = None
        return rates

    def fetch_mcx_gold(self) -> dict:
        """
        Fetch MCX (INR-denominated) data for the active metal.
        Uses the NSE ETF proxy from the asset config (GOLDBEES.NS for gold,
        SILVERBEES.NS for silver). Also fetches USD/INR for conversion context.
        The Indian ETF dataframe is stored under the "goldbees" key for
        backward compatibility with the downstream engines.
        """
        mcx_data = {}
        proxy_ticker = self.asset_cfg["mcx"]["proxy_ticker"]
        proxy_label = self.asset_cfg["mcx"]["proxy_label"]

        # NSE ETF proxy (GOLDBEES / SILVERBEES) for the MCX Mini contract
        try:
            goldbees = yf.download(proxy_ticker, start=self.start_6m,
                                  end=self.end_date, interval="1d", progress=False)
            if isinstance(goldbees.columns, pd.MultiIndex):
                goldbees.columns = goldbees.columns.get_level_values(0)
            mcx_data["goldbees"] = goldbees
        except Exception as e:
            print(f"  WARNING: {proxy_label} data error: {e}")
            mcx_data["goldbees"] = pd.DataFrame()
        
        # USD/INR exchange rate
        try:
            usdinr = yf.download("USDINR=X", start=self.start_3m, 
                                end=self.end_date, interval="1d", progress=False)
            if isinstance(usdinr.columns, pd.MultiIndex):
                usdinr.columns = usdinr.columns.get_level_values(0)
            mcx_data["usdinr"] = usdinr
        except Exception as e:
            print(f"  ⚠ USD/INR data error: {e}")
            mcx_data["usdinr"] = pd.DataFrame()
        
        # Calculate MCX Gold equivalent (approximate)
        # MCX Gold = International Gold (per troy oz) * USDINR / 31.1035 * 10 (per 10 grams)
        try:
            if not mcx_data["usdinr"].empty:
                usdinr_rate = float(mcx_data["usdinr"]["Close"].iloc[-1])
                mcx_data["usdinr_rate"] = usdinr_rate
            else:
                mcx_data["usdinr_rate"] = 85.0  # fallback
        except:
            mcx_data["usdinr_rate"] = 85.0
        
        return mcx_data
    
    def fetch_cross_assets(self) -> dict:
        """Fetch all cross-asset data for correlation analysis."""
        cross_data = {}
        
        for name, ticker in self.cross_assets.items():
            try:
                df = yf.download(ticker, start=self.start_6m, end=self.end_date, 
                                interval="1d", progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                cross_data[name] = df
            except Exception as e:
                print(f"  ⚠ {name} data error: {e}")
                cross_data[name] = pd.DataFrame()
        
        return cross_data
    
    def fetch_dxy_latest(self) -> float:
        """Get latest DXY value."""
        try:
            dxy = yf.download("DX-Y.NYB", period="5d", interval="1d", progress=False)
            if isinstance(dxy.columns, pd.MultiIndex):
                dxy.columns = dxy.columns.get_level_values(0)
            return float(dxy["Close"].iloc[-1]) if not dxy.empty else None
        except:
            return None
    
    def fetch_vix_latest(self) -> float:
        """Get latest VIX value."""
        try:
            vix = yf.download("^VIX", period="5d", interval="1d", progress=False)
            if isinstance(vix.columns, pd.MultiIndex):
                vix.columns = vix.columns.get_level_values(0)
            return float(vix["Close"].iloc[-1]) if not vix.empty else None
        except:
            return None
    
    def fetch_treasury_yields(self) -> dict:
        """Get latest treasury yields for macro analysis."""
        yields = {}
        
        # 10-Year
        try:
            tnx = yf.download("^TNX", period="5d", interval="1d", progress=False)
            if isinstance(tnx.columns, pd.MultiIndex):
                tnx.columns = tnx.columns.get_level_values(0)
            yields["US10Y"] = float(tnx["Close"].iloc[-1]) if not tnx.empty else None
        except:
            yields["US10Y"] = None
        
        # 2-Year (using 13-week T-Bill as proxy)
        try:
            irx = yf.download("^IRX", period="5d", interval="1d", progress=False)
            if isinstance(irx.columns, pd.MultiIndex):
                irx.columns = irx.columns.get_level_values(0)
            yields["US02Y"] = float(irx["Close"].iloc[-1]) if not irx.empty else None
        except:
            yields["US02Y"] = None
        
        # Yield curve spread
        if yields.get("US10Y") and yields.get("US02Y"):
            yields["curve_spread"] = yields["US10Y"] - yields["US02Y"]
        else:
            yields["curve_spread"] = None
        
        return yields
    
    def read_existing_sentiment(self) -> dict:
        """
        Read pre-collected sentiment data from Data Collection pipeline.
        Looks for latest parquet files in sentiment_data directory.
        """
        sentiment = {}
        
        base = Path(__file__).resolve().parent.parent.parent / "Data collection" / "data" / "raw" / "sentiment_data"
        
        # Fear & Greed
        try:
            fg_path = base / "fear_greed_index_latest.parquet"
            if fg_path.exists():
                sentiment["fear_greed"] = pd.read_parquet(fg_path)
        except Exception as e:
            print(f"  ⚠ Fear & Greed read error: {e}")
        
        # News sentiment
        try:
            ns_path = base / "news_sentiment_latest.parquet"
            if ns_path.exists():
                sentiment["news_sentiment"] = pd.read_parquet(ns_path)
        except Exception as e:
            print(f"  ⚠ News sentiment read error: {e}")
        
        # Keyword sentiment
        try:
            ks_path = base / "keyword_sentiment_summary_latest.parquet"
            if ks_path.exists():
                sentiment["keyword_sentiment"] = pd.read_parquet(ks_path)
        except Exception as e:
            print(f"  ⚠ Keyword sentiment read error: {e}")
        
        # VIX term structure
        try:
            vix_path = base / "vix_term_structure_latest.parquet"
            if vix_path.exists():
                sentiment["vix_term_structure"] = pd.read_parquet(vix_path)
        except Exception as e:
            print(f"  ⚠ VIX term structure read error: {e}")
        
        # Fear & Greed history
        try:
            fgh_path = base / "fear_greed_historical_latest.parquet"
            if fgh_path.exists():
                sentiment["fear_greed_history"] = pd.read_parquet(fgh_path)
        except Exception as e:
            print(f"  ⚠ Fear & Greed history read error: {e}")
        
        return sentiment
    
    def read_existing_options(self) -> pd.DataFrame:
        """Read options chain data from pipeline."""
        try:
            opts_path = (Path(__file__).resolve().parent.parent.parent / 
                        "Data collection" / "data" / "raw" / "financial_data" / 
                        "options_chains_latest.parquet")
            if opts_path.exists():
                return pd.read_parquet(opts_path)
        except Exception as e:
            print(f"  ⚠ Options data read error: {e}")
        return pd.DataFrame()
    
    def read_existing_signals(self) -> dict:
        """Read the latest composite signal from pipeline."""
        try:
            signals_dir = (Path(__file__).resolve().parent.parent.parent / 
                          "Data collection" / "data" / "signals")
            signal_files = sorted(signals_dir.glob("composite_alpha_*.json"), reverse=True)
            if signal_files:
                with open(signal_files[0], 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"  ⚠ Signals read error: {e}")
        return {}
    
    def fetch_world_indices(self) -> list:
        """
        Snapshot of major global equity indices for the World Indices panel,
        Finviz-style: last price, daily % change, and an intraday sparkline of
        the latest session. Two batched downloads (daily for %, intraday for the
        sparkline).
        Returns [{name, symbol, region, price, change_pct, spark[]}].
        """
        symbols = [s for _, s, _ in WORLD_INDICES]
        daily = intra = None
        try:
            daily = yf.download(" ".join(symbols), period="7d", interval="1d",
                                progress=False, group_by="ticker")
        except Exception as e:
            print(f"  WARNING: World indices (daily) error: {e}")
        try:
            intra = yf.download(" ".join(symbols), period="1d", interval="5m",
                                progress=False, group_by="ticker")
        except Exception as e:
            print(f"  WARNING: World indices (intraday) error: {e}")

        def _closes(df, sym):
            try:
                if df is None:
                    return None
                if isinstance(df.columns, pd.MultiIndex):
                    if sym not in df.columns.get_level_values(0):
                        return None
                    sub = df[sym]
                else:
                    sub = df  # single-ticker fallback
                if "Close" not in sub.columns:
                    return None
                return sub["Close"].dropna()
            except Exception:
                return None

        out = []
        for name, sym, region in WORLD_INDICES:
            price, chg, spark = None, None, []
            dclose = _closes(daily, sym)
            if dclose is not None and len(dclose) >= 2:
                price = float(dclose.iloc[-1])
                prev = float(dclose.iloc[-2])
                chg = (price - prev) / prev * 100 if prev else None
            elif dclose is not None and len(dclose) == 1:
                price = float(dclose.iloc[-1])

            # Intraday sparkline (downsampled to <= 48 points).
            iclose = _closes(intra, sym)
            if iclose is not None and len(iclose) >= 3:
                vals = [float(x) for x in iclose.tolist()]
                if len(vals) > 48:
                    step = max(1, len(vals) // 48)
                    vals = vals[::step]
                spark = [round(v, 2) for v in vals]
                if price is None:
                    price = spark[-1]
            elif dclose is not None and len(dclose) >= 3:
                # Fall back to a few daily closes if intraday is unavailable.
                spark = [round(float(x), 2) for x in dclose.tail(7).tolist()]

            out.append({
                "name": name,
                "symbol": sym,
                "region": region,
                "price": round(price, 2) if price is not None else None,
                "change_pct": round(chg, 2) if chg is not None else None,
                "spark": spark,
            })
        return out

    def fetch_all(self) -> dict:
        """
        Master fetch — get all data needed for pre-session analysis.
        """
        name = self.asset_cfg["name"]
        print(f"[DATA] Fetching {name} data...")

        data = {}

        print(f"  > {name} multi-timeframe (1H, 4H, Daily)...")
        data["gold"] = self.fetch_gold_multi_timeframe()

        print(f"  > {name} long history (ML / seasonality / backtest)...")
        data["gold_long"] = self.fetch_gold_long_history()

        print(f"  > {name} full chart history (max, for long-range chart)...")
        data["gold_chart"] = self.fetch_chart_history()

        print(f"  > FX rates ({name} in EUR / JPY / GBP)...")
        data["fx"] = self.fetch_fx_rates()

        if self.asset_class != "metal":
            data["mcx"] = {}  # no MCX/India contract for crypto or indices
        else:
            print(f"  > {self.asset_cfg['mcx']['name']} / India data...")
            data["mcx"] = self.fetch_mcx_gold()

        print("  > World indices snapshot...")
        data["world_indices"] = self.fetch_world_indices()
        
        print("  > Cross-asset universe...")
        data["cross_assets"] = self.fetch_cross_assets()
        
        print("  > Macro indicators...")
        data["dxy"] = self.fetch_dxy_latest()
        data["vix"] = self.fetch_vix_latest()
        data["yields"] = self.fetch_treasury_yields()
        
        print("  > Existing pipeline sentiment data...")
        data["sentiment"] = self.read_existing_sentiment()
        
        print("  > Existing pipeline options data...")
        data["options"] = self.read_existing_options()
        
        print("  > Existing composite signals...")
        data["pipeline_signals"] = self.read_existing_signals()
        
        print("  [OK] Data fetch complete\n")
        
        return data
