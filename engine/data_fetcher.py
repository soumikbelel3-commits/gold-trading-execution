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

warnings.filterwarnings("ignore")

# Path to existing data collection pipeline
DATA_COLLECTION_DIR = Path(__file__).resolve().parent.parent.parent / "Data collection" / "data" / "raw"
SENTIMENT_DIR = DATA_COLLECTION_DIR.parent / "raw" / "sentiment_data"


class GoldDataFetcher:
    """
    Fetches gold and cross-asset data from multiple sources.
    
    Primary: yfinance (live)
    Secondary: Existing parquet files from Data Collection pipeline
    """
    
    def __init__(self):
        self.end_date = datetime.now()
        self.start_1y = self.end_date - timedelta(days=365)
        self.start_6m = self.end_date - timedelta(days=180)
        self.start_3m = self.end_date - timedelta(days=90)
        self.start_1m = self.end_date - timedelta(days=30)
        
        # Cross-asset universe
        self.cross_assets = {
            "DXY": "DX-Y.NYB",
            "US10Y": "^TNX",
            "US02Y": "^IRX",
            "SPY": "SPY",
            "TLT": "TLT",
            "CrudeOil": "CL=F",
            "Silver": "SI=F",
            "BTC": "BTC-USD",
            "VIX": "^VIX",
            "GLD_ETF": "GLD",
        }
    
    def fetch_gold_multi_timeframe(self) -> dict:
        """
        Fetch gold futures data at multiple timeframes.
        Returns dict with keys: '1h', '4h', 'daily'
        """
        result = {}
        
        # Daily — 1 year
        try:
            daily = yf.download("GC=F", start=self.start_1y, end=self.end_date, 
                               interval="1d", progress=False)
            if isinstance(daily.columns, pd.MultiIndex):
                daily.columns = daily.columns.get_level_values(0)
            result["daily"] = daily
        except Exception as e:
            print(f"  ⚠ Daily gold data error: {e}")
            result["daily"] = pd.DataFrame()
        
        # 1-Hour — 60 days (yfinance limit for 1h)
        try:
            h1 = yf.download("GC=F", period="60d", interval="1h", progress=False)
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
    
    def fetch_mcx_gold(self) -> dict:
        """
        Fetch MCX Gold data (INR-denominated gold futures proxy).
        Uses GOLDBEES.NS (Gold ETF on NSE) as proxy for MCX Gold.
        Also fetches USD/INR for conversion context.
        """
        mcx_data = {}
        
        # GOLDBEES — Indian gold ETF (proxy for MCX Gold Mini)
        try:
            goldbees = yf.download("GOLDBEES.NS", start=self.start_6m, 
                                  end=self.end_date, interval="1d", progress=False)
            if isinstance(goldbees.columns, pd.MultiIndex):
                goldbees.columns = goldbees.columns.get_level_values(0)
            mcx_data["goldbees"] = goldbees
        except Exception as e:
            print(f"  ⚠ GOLDBEES data error: {e}")
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
    
    def fetch_all(self) -> dict:
        """
        Master fetch — get all data needed for pre-session analysis.
        """
        print("[DATA] Fetching data...")
        
        data = {}
        
        print("  > Gold multi-timeframe (1H, 4H, Daily)...")
        data["gold"] = self.fetch_gold_multi_timeframe()
        
        print("  > MCX Gold / India data...")
        data["mcx"] = self.fetch_mcx_gold()
        
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
