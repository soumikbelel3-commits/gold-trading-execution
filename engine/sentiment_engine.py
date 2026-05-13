"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Sentiment Engine                      ║
║   Reads existing pipeline data, aggregates sentiment signals     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
from pathlib import Path


class GoldSentimentEngine:
    """
    Aggregates sentiment data from the existing Data Collection pipeline.
    Reads parquet files and computes gold-specific sentiment score.
    """
    
    def __init__(self, sentiment_data: dict):
        """
        Args:
            sentiment_data: dict from data_fetcher.read_existing_sentiment()
        """
        self.data = sentiment_data
    
    def analyze(self) -> dict:
        """Run full sentiment analysis."""
        result = {
            "fear_greed": self._analyze_fear_greed(),
            "news_sentiment": self._analyze_news_sentiment(),
            "keyword_sentiment": self._analyze_keyword_sentiment(),
            "composite_score": 0,
            "composite_label": "Neutral",
        }
        
        # Compute composite
        scores = []
        weights = []
        
        fg = result["fear_greed"]
        if fg.get("score") is not None:
            # Convert 0-100 to -1 to +1
            normalized = (fg["score"] - 50) / 50
            scores.append(normalized)
            weights.append(0.35)
        
        ns = result["news_sentiment"]
        if ns.get("gold_sentiment") is not None:
            scores.append(ns["gold_sentiment"])
            weights.append(0.40)
        
        ks = result["keyword_sentiment"]
        if ks.get("avg_score") is not None:
            scores.append(ks["avg_score"])
            weights.append(0.25)
        
        if scores and weights:
            total_w = sum(weights)
            composite = sum(s * w for s, w in zip(scores, weights)) / total_w
            result["composite_score"] = round(composite, 4)
            
            if composite > 0.3:
                result["composite_label"] = "Strong Bullish Sentiment"
            elif composite > 0.1:
                result["composite_label"] = "Bullish Sentiment"
            elif composite > -0.1:
                result["composite_label"] = "Neutral Sentiment"
            elif composite > -0.3:
                result["composite_label"] = "Bearish Sentiment"
            else:
                result["composite_label"] = "Strong Bearish Sentiment"
        
        return result
    
    def _analyze_fear_greed(self) -> dict:
        """Analyze Fear & Greed Index data."""
        fg_df = self.data.get("fear_greed")
        if fg_df is None or (hasattr(fg_df, 'empty') and fg_df.empty):
            return {"score": None, "label": "No data", "detail": "Fear & Greed data not available"}
        
        try:
            # Try to extract the index value
            if 'value' in fg_df.columns:
                score = float(fg_df['value'].iloc[-1])
            elif 'score' in fg_df.columns:
                score = float(fg_df['score'].iloc[-1])
            elif len(fg_df.columns) > 0:
                # Try first numeric column
                for col in fg_df.columns:
                    if fg_df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                        score = float(fg_df[col].iloc[-1])
                        break
                else:
                    return {"score": None, "label": "No data", "detail": "Could not parse Fear & Greed"}
            
            # Classify
            if score <= 20:
                label = "Extreme Fear"
            elif score <= 40:
                label = "Fear"
            elif score <= 60:
                label = "Neutral"
            elif score <= 80:
                label = "Greed"
            else:
                label = "Extreme Greed"
            
            # For gold: extreme fear = bullish (safe haven), extreme greed = bearish
            gold_implication = ""
            if score <= 30:
                gold_implication = "Extreme fear → strong safe-haven demand for gold"
            elif score <= 45:
                gold_implication = "Fear → mild gold support"
            elif score <= 55:
                gold_implication = "Neutral sentiment → no clear gold direction"
            elif score <= 75:
                gold_implication = "Greed → risk-on, less gold demand"
            else:
                gold_implication = "Extreme greed → gold may see selling pressure"
            
            return {
                "score": score,
                "label": label,
                "gold_implication": gold_implication,
            }
        except Exception as e:
            return {"score": None, "label": "Error", "detail": str(e)}
    
    def _analyze_news_sentiment(self) -> dict:
        """Analyze news sentiment data for gold-related keywords."""
        ns_df = self.data.get("news_sentiment")
        if ns_df is None or (hasattr(ns_df, 'empty') and ns_df.empty):
            return {"gold_sentiment": None, "headlines": [], "detail": "No news data"}
        
        try:
            result = {"gold_sentiment": None, "headlines": [], "article_count": 0}
            
            # Find sentiment column
            sent_col = None
            for col in ['vader_compound', 'sentiment_score', 'compound', 'sentiment']:
                if col in ns_df.columns:
                    sent_col = col
                    break
            
            if sent_col is None:
                # Try first numeric column
                for col in ns_df.columns:
                    if ns_df[col].dtype in ['float64', 'float32']:
                        sent_col = col
                        break
            
            # Find title/headline column
            title_col = None
            for col in ['title', 'headline', 'text', 'description']:
                if col in ns_df.columns:
                    title_col = col
                    break
            
            # Filter for gold-related news
            gold_keywords = ['gold', 'bullion', 'precious metal', 'xau', 'safe haven', 
                           'central bank', 'fed', 'inflation', 'treasury', 'yield']
            
            if title_col:
                mask = ns_df[title_col].str.lower().str.contains(
                    '|'.join(gold_keywords), na=False
                )
                gold_news = ns_df[mask]
            else:
                gold_news = ns_df  # Use all if no title column
            
            result["article_count"] = len(gold_news)
            
            if sent_col and not gold_news.empty:
                avg_sentiment = float(gold_news[sent_col].mean())
                result["gold_sentiment"] = round(avg_sentiment, 4)
                
                # Get top headlines
                if title_col:
                    for _, row in gold_news.head(5).iterrows():
                        headline = str(row[title_col])[:120]
                        sent = float(row[sent_col]) if sent_col else 0
                        result["headlines"].append({
                            "title": headline,
                            "sentiment": round(sent, 3)
                        })
            elif sent_col:
                result["gold_sentiment"] = round(float(ns_df[sent_col].mean()), 4)
            
            return result
        except Exception as e:
            return {"gold_sentiment": None, "headlines": [], "detail": str(e)}
    
    def _analyze_keyword_sentiment(self) -> dict:
        """Analyze keyword-level sentiment data."""
        ks_df = self.data.get("keyword_sentiment")
        if ks_df is None or (hasattr(ks_df, 'empty') and ks_df.empty):
            return {"avg_score": None, "detail": "No keyword data"}
        
        try:
            # Try to extract scores
            score_col = None
            for col in ['avg_sentiment', 'sentiment', 'score', 'compound']:
                if col in ks_df.columns:
                    score_col = col
                    break
            
            if score_col is None:
                for col in ks_df.columns:
                    if ks_df[col].dtype in ['float64', 'float32']:
                        score_col = col
                        break
            
            if score_col:
                avg = float(ks_df[score_col].mean())
                return {
                    "avg_score": round(avg, 4),
                    "keyword_count": len(ks_df),
                }
            
            return {"avg_score": None, "detail": "No score column found"}
        except Exception as e:
            return {"avg_score": None, "detail": str(e)}
