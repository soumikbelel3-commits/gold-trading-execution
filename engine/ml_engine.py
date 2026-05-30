"""
╔══════════════════════════════════════════════════════════════════╗
║         Gold Pre-Session — Machine Learning Engine               ║
║   Walk-forward ensemble predicting next-session direction        ║
╚══════════════════════════════════════════════════════════════════╝

Trains a small ensemble (Random Forest + Gradient Boosting + Logistic
Regression) on engineered technical features from a multi-year gold history
to estimate the probability of an up day next session. Validation is strictly
walk-forward (no look-ahead) and reported out-of-sample.
"""

import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score, roc_auc_score
    SKLEARN = True
except Exception:
    SKLEARN = False


class GoldMLEngine:
    """Predicts next-session direction with a validated ML ensemble."""

    FEATURES = [
        "ret_1", "ret_2", "ret_3", "ret_5", "ret_10",
        "rsi", "macd_hist", "bb_pos", "atr_pct", "vol_ratio",
        "dist_sma20", "dist_sma50", "dist_sma200", "roc_10", "mom_20",
        "dow", "month",
    ]

    def __init__(self, gold_long: pd.DataFrame, horizon: int = 1):
        self.df = gold_long if gold_long is not None else pd.DataFrame()
        self.horizon = horizon

    def analyze(self) -> dict:
        result = {"available": False, "reason": ""}
        if not SKLEARN:
            result["reason"] = "scikit-learn not installed"
            return result
        if self.df.empty or "Close" not in self.df.columns or len(self.df) < 400:
            result["reason"] = "Insufficient history for ML"
            return result

        feat = self._build_features()
        if feat is None or len(feat) < 300:
            result["reason"] = "Not enough clean feature rows"
            return result

        X = feat[self.FEATURES].values
        y = feat["target"].values

        # ── Walk-forward out-of-sample validation ──
        tscv = TimeSeriesSplit(n_splits=5)
        models = {
            "Random Forest": RandomForestClassifier(
                n_estimators=200, max_depth=5, min_samples_leaf=20,
                random_state=42, n_jobs=-1),
            "Gradient Boosting": GradientBoostingClassifier(
                n_estimators=150, max_depth=3, learning_rate=0.05,
                random_state=42),
            "Logistic Regression": make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=1000, C=0.5)),
        }

        model_scores = {name: {"acc": [], "auc": []} for name in models}
        ens_acc, ens_auc = [], []
        for tr, te in tscv.split(X):
            if len(np.unique(y[tr])) < 2:
                continue
            fold_probs = []
            for name, mdl in models.items():
                mdl.fit(X[tr], y[tr])
                p = mdl.predict_proba(X[te])[:, 1]
                fold_probs.append(p)
                pred = (p >= 0.5).astype(int)
                model_scores[name]["acc"].append(accuracy_score(y[te], pred))
                try:
                    model_scores[name]["auc"].append(roc_auc_score(y[te], p))
                except ValueError:
                    pass
            ens_p = np.mean(fold_probs, axis=0)
            ens_acc.append(accuracy_score(y[te], (ens_p >= 0.5).astype(int)))
            try:
                ens_auc.append(roc_auc_score(y[te], ens_p))
            except ValueError:
                pass

        result["models"] = []
        for name, sc in model_scores.items():
            if sc["acc"]:
                result["models"].append({
                    "name": name,
                    "accuracy": round(float(np.mean(sc["acc"])) * 100, 1),
                    "auc": round(float(np.mean(sc["auc"])), 3) if sc["auc"] else None,
                })

        baseline = max(float(np.mean(y)), 1 - float(np.mean(y))) * 100
        result["ensemble"] = {
            "accuracy": round(float(np.mean(ens_acc)) * 100, 1) if ens_acc else None,
            "auc": round(float(np.mean(ens_auc)), 3) if ens_auc else None,
            "baseline_accuracy": round(baseline, 1),
        }

        # ── Refit on all data, predict the next session ──
        latest = X[-1].reshape(1, -1)
        probs = []
        rf = None
        for name, mdl in models.items():
            mdl.fit(X[:-1], y[:-1]) if len(X) > 1 else mdl.fit(X, y)
            probs.append(float(mdl.predict_proba(latest)[0, 1]))
            if name == "Random Forest":
                rf = mdl
        prob_up = float(np.mean(probs)) * 100

        direction = "UP" if prob_up >= 50 else "DOWN"
        conf = abs(prob_up - 50) * 2  # 0..100
        result["prediction"] = {
            "prob_up": round(prob_up, 1),
            "prob_down": round(100 - prob_up, 1),
            "direction": direction,
            "confidence": round(conf, 1),
            "per_model": [{"name": n, "prob_up": round(p * 100, 1)}
                          for n, p in zip(models.keys(), probs)],
            "horizon_days": self.horizon,
        }

        # ── Feature importance (from Random Forest) ──
        if rf is not None and hasattr(rf, "feature_importances_"):
            imp = sorted(zip(self.FEATURES, rf.feature_importances_),
                         key=lambda x: x[1], reverse=True)
            result["feature_importance"] = [
                {"feature": self._pretty(f), "importance": round(float(v) * 100, 1)}
                for f, v in imp[:10]
            ]

        result["available"] = True
        result["samples"] = int(len(feat))
        result["target"] = f"Direction of gold close in {self.horizon} session(s)"
        return result

    # ──────────────────────────────────────────────
    def _build_features(self):
        close = self.df["Close"].squeeze() if isinstance(self.df["Close"], pd.DataFrame) else self.df["Close"]
        high = self.df["High"].squeeze() if "High" in self.df.columns else close
        low = self.df["Low"].squeeze() if "Low" in self.df.columns else close
        vol = self.df["Volume"].squeeze() if "Volume" in self.df.columns else pd.Series(0, index=close.index)
        d = pd.DataFrame({"close": close, "high": high, "low": low, "vol": vol}).dropna(subset=["close"])
        d.index = pd.to_datetime(d.index)

        for n in [1, 2, 3, 5, 10]:
            d[f"ret_{n}"] = d["close"].pct_change(n) * 100

        delta = d["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta).where(delta < 0, 0.0).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        d["rsi"] = 100 - (100 / (1 + rs))

        ema12 = d["close"].ewm(span=12).mean()
        ema26 = d["close"].ewm(span=26).mean()
        macd = ema12 - ema26
        d["macd_hist"] = macd - macd.ewm(span=9).mean()

        bb_sma = d["close"].rolling(20).mean()
        bb_std = d["close"].rolling(20).std()
        d["bb_pos"] = (d["close"] - (bb_sma - 2 * bb_std)) / (4 * bb_std).replace(0, np.nan)

        tr = pd.concat([d["high"] - d["low"],
                        (d["high"] - d["close"].shift()).abs(),
                        (d["low"] - d["close"].shift()).abs()], axis=1).max(axis=1)
        d["atr_pct"] = tr.rolling(14).mean() / d["close"] * 100

        vol_sma = d["vol"].rolling(20).mean()
        d["vol_ratio"] = (d["vol"] / vol_sma.replace(0, np.nan)).fillna(1.0)

        for p in [20, 50, 200]:
            sma = d["close"].rolling(p).mean()
            d[f"dist_sma{p}"] = (d["close"] - sma) / sma * 100

        d["roc_10"] = (d["close"] / d["close"].shift(10) - 1) * 100
        d["mom_20"] = (d["close"] / d["close"].shift(20) - 1) * 100
        d["dow"] = d.index.dayofweek
        d["month"] = d.index.month

        d["target"] = (d["close"].shift(-self.horizon) > d["close"]).astype(int)
        d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=self.FEATURES + ["target"])
        # Drop the final `horizon` rows where target is undefined (shift produced NaN -> already dropped)
        return d

    @staticmethod
    def _pretty(f):
        names = {
            "ret_1": "1d Return", "ret_2": "2d Return", "ret_3": "3d Return",
            "ret_5": "5d Return", "ret_10": "10d Return", "rsi": "RSI(14)",
            "macd_hist": "MACD Histogram", "bb_pos": "Bollinger Position",
            "atr_pct": "ATR %", "vol_ratio": "Volume Ratio",
            "dist_sma20": "Dist. SMA20", "dist_sma50": "Dist. SMA50",
            "dist_sma200": "Dist. SMA200", "roc_10": "ROC(10)",
            "mom_20": "Momentum(20)", "dow": "Day of Week", "month": "Month",
        }
        return names.get(f, f)
