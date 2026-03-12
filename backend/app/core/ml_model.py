"""
ML Signal Classifier
Uses Random Forest to classify high/low probability trades
Trained on historical XAUUSD data
"""
import os
import logging
import pickle
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

logger = logging.getLogger(__name__)

MODEL_PATH = Path("models/signal_classifier.pkl")
SCALER_PATH = Path("models/scaler.pkl")


class SignalClassifier:
    """
    ML model to filter trading signals.
    Labels:
      1 = High probability trade (predicted winner)
      0 = Low probability trade (skip)
    """

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self._load_model()

    def _load_model(self):
        """Load pre-trained model if available."""
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            logger.info("Loaded pre-trained signal classifier")

    def _save_model(self):
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("Saved trained model")

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract ML features from OHLCV + indicator dataframe."""
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df.get("tick_volume", pd.Series([0] * len(df)))

        features = pd.DataFrame()

        # Price momentum features
        for period in [5, 10, 20]:
            features[f"return_{period}"] = close.pct_change(period)
            features[f"hl_ratio_{period}"] = (high.rolling(period).max() - low.rolling(period).min()) / close

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        features["rsi"] = 100 - (100 / (1 + rs))

        # MA relationships
        for p in [10, 20, 50]:
            ema = close.ewm(span=p).mean()
            features[f"close_vs_ema{p}"] = (close - ema) / ema

        # ATR normalized
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = tr.ewm(span=14).mean()
        features["atr_pct"] = atr / close

        # Bollinger band position
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        features["bb_position"] = (close - bb_mid) / (2 * bb_std)

        # Volume features
        features["volume_ratio"] = volume / volume.rolling(20).mean()

        # Candlestick patterns
        features["body_size"] = abs(close - df["open"]) / atr
        features["upper_wick"] = (high - close.clip(upper=df["open"])) / atr
        features["lower_wick"] = (close.clip(lower=df["open"]) - low) / atr

        return features.dropna()

    def prepare_labels(self, df: pd.DataFrame, forward_periods: int = 5, min_return: float = 0.002) -> pd.Series:
        """
        Create binary labels: 1 if price moved favorably by min_return
        forward_periods candles ahead.
        """
        future_return = df["close"].shift(-forward_periods) / df["close"] - 1
        return (future_return.abs() >= min_return).astype(int)

    def train(self, df: pd.DataFrame) -> dict:
        """Train the classifier on historical data."""
        logger.info("Training signal classifier...")

        features = self.extract_features(df)
        labels = self.prepare_labels(df, forward_periods=5, min_return=0.003)

        # Align
        common_idx = features.index.intersection(labels.index)
        X = features.loc[common_idx].dropna()
        y = labels.loc[X.index]

        if len(X) < 100:
            raise ValueError(f"Insufficient data for training: {len(X)} samples")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)

        logger.info(f"Model accuracy: {accuracy:.3f} | CV: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

        self._save_model()

        return {
            "accuracy": round(accuracy, 4),
            "cv_mean": round(cv_scores.mean(), 4),
            "cv_std": round(cv_scores.std(), 4),
            "samples_trained": len(X_train),
            "report": classification_report(y_test, y_pred, output_dict=True),
        }

    def predict(self, df: pd.DataFrame) -> Tuple[int, float]:
        """
        Predict signal quality for the latest candle.
        Returns (prediction: 0|1, confidence: 0.0-1.0)
        """
        if self.model is None or self.scaler is None:
            return 1, 0.5  # Default: allow trade, 50% confidence

        features = self.extract_features(df)
        if features.empty:
            return 1, 0.5

        X = features.iloc[[-1]]
        X_scaled = self.scaler.transform(X)

        pred = int(self.model.predict(X_scaled)[0])
        confidence = float(self.model.predict_proba(X_scaled)[0][pred])

        return pred, confidence

    def is_high_probability(self, df: pd.DataFrame, min_confidence: float = 0.6) -> bool:
        """Returns True if the current signal is high probability."""
        pred, confidence = self.predict(df)
        return pred == 1 and confidence >= min_confidence
