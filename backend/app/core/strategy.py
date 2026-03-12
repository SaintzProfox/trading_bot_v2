"""
Trading Strategy: RSI + MA Crossover + ATR
Configurable parameters for XAUUSD
"""
import pandas as pd
import numpy as np
from typing import Optional


class TradingStrategy:
    """
    Multi-indicator strategy:
    - RSI for overbought/oversold
    - MA crossover for trend direction
    - ATR for dynamic SL/TP calculation
    """

    def __init__(self, settings: dict):
        self.settings = settings

    def generate_signal(self, df: pd.DataFrame) -> Optional[dict]:
        """Analyze price data and return trade signal or None."""
        df = self._calculate_indicators(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        rsi = latest["rsi"]
        fast_ma = latest["fast_ma"]
        slow_ma = latest["slow_ma"]
        prev_fast = prev["fast_ma"]
        prev_slow = prev["slow_ma"]
        atr = latest["atr"]

        # Trend filter
        trend = "bullish" if fast_ma > slow_ma else "bearish"

        # MA Crossover signals
        bullish_cross = prev_fast <= prev_slow and fast_ma > slow_ma
        bearish_cross = prev_fast >= prev_slow and fast_ma < slow_ma

        # RSI filters
        rsi_oversold = rsi < self.settings.get("rsi_oversold", 30)
        rsi_overbought = rsi > self.settings.get("rsi_overbought", 70)
        rsi_mid_bull = 40 < rsi < 60 and trend == "bullish"
        rsi_mid_bear = 40 < rsi < 60 and trend == "bearish"

        direction = None
        if bullish_cross and (rsi_oversold or rsi_mid_bull):
            direction = "BUY"
        elif bearish_cross and (rsi_overbought or rsi_mid_bear):
            direction = "SELL"

        if direction is None:
            return None

        # ATR-based SL/TP
        atr_multiplier_sl = self.settings.get("atr_multiplier_sl", 1.5)
        atr_multiplier_tp = self.settings.get("atr_multiplier_tp", 2.5)
        price = df.iloc[-1]["close"]

        if direction == "BUY":
            stop_loss = price - (atr * atr_multiplier_sl)
            take_profit = price + (atr * atr_multiplier_tp)
        else:
            stop_loss = price + (atr * atr_multiplier_sl)
            take_profit = price - (atr * atr_multiplier_tp)

        # Calculate signal strength 0-100
        signal_strength = self._calculate_signal_strength(df, direction)

        return {
            "direction": direction,
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "strategy": "RSI_MA_ATR",
            "signal_strength": signal_strength,
            "rsi": round(rsi, 2),
            "atr": round(atr, 2),
            "trend": trend,
        }

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute RSI, MA, ATR on price dataframe."""
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # RSI
        rsi_period = self.settings.get("rsi_period", 14)
        df["rsi"] = self._rsi(close, rsi_period)

        # Moving Averages
        fast_period = self.settings.get("fast_ma_period", 20)
        slow_period = self.settings.get("slow_ma_period", 50)
        ma_type = self.settings.get("ma_type", "EMA")

        if ma_type == "EMA":
            df["fast_ma"] = close.ewm(span=fast_period).mean()
            df["slow_ma"] = close.ewm(span=slow_period).mean()
        else:
            df["fast_ma"] = close.rolling(fast_period).mean()
            df["slow_ma"] = close.rolling(slow_period).mean()

        # ATR
        atr_period = self.settings.get("atr_period", 14)
        df["atr"] = self._atr(high, low, close, atr_period)

        # Bollinger Bands (optional filter)
        bb_period = self.settings.get("bb_period", 20)
        df["bb_upper"], df["bb_lower"] = self._bollinger_bands(close, bb_period)

        return df

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.ewm(span=period).mean()

    @staticmethod
    def _bollinger_bands(series: pd.Series, period: int = 20, std: float = 2.0):
        sma = series.rolling(period).mean()
        std_dev = series.rolling(period).std()
        return sma + (std * std_dev), sma - (std * std_dev)

    def _calculate_signal_strength(self, df: pd.DataFrame, direction: str) -> float:
        """Score signal strength 0-100 based on confluence."""
        score = 0
        latest = df.iloc[-1]
        rsi = latest["rsi"]

        if direction == "BUY":
            if rsi < 40:
                score += 30
            if rsi < 30:
                score += 20
            if latest["fast_ma"] > latest["slow_ma"]:
                score += 25
            if latest["close"] > latest["bb_upper"] * 0.98:
                score += 25
        else:
            if rsi > 60:
                score += 30
            if rsi > 70:
                score += 20
            if latest["fast_ma"] < latest["slow_ma"]:
                score += 25
            if latest["close"] < latest["bb_lower"] * 1.02:
                score += 25

        return min(score, 100)
