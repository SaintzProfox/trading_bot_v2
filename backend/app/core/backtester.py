"""
Backtesting Engine for XAUUSD Strategy
Simulates trades on historical data with full metrics
"""
import logging
from datetime import datetime
from typing import List, Optional
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from app.core.strategy import TradingStrategy

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Vectorized backtesting engine.
    Simulates RSI+MA+ATR strategy on historical XAUUSD data.
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.strategy = TradingStrategy(settings)

    def fetch_historical_data(
        self,
        symbol: str = "XAUUSD",
        timeframe: int = mt5.TIMEFRAME_H1,
        start: Optional[datetime] = None,
        bars: int = 5000,
    ) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data from MT5."""
        if not mt5.initialize():
            logger.error("MT5 not initialized")
            return None

        if start:
            rates = mt5.copy_rates_from(symbol, timeframe, start, bars)
        else:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)

        if rates is None:
            return None

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df

    def run(self, df: pd.DataFrame, initial_balance: float = 10000.0) -> dict:
        """
        Run backtest simulation on provided dataframe.
        Returns comprehensive performance metrics.
        """
        df = df.copy()
        trades = []
        balance = initial_balance
        equity_curve = [initial_balance]

        # Calculate all indicators upfront
        df = self.strategy._calculate_indicators(df)
        df = df.dropna()

        open_trade = None

        for i in range(50, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i - 1]

            # Check if open trade should be closed
            if open_trade is not None:
                closed, pnl = self._check_trade_close(open_trade, row)
                if closed:
                    balance += pnl
                    open_trade["exit_price"] = row["close"]
                    open_trade["exit_time"] = row["time"]
                    open_trade["pnl"] = pnl
                    open_trade["status"] = "closed"
                    trades.append(open_trade)
                    open_trade = None
                    equity_curve.append(balance)
                    continue

            # Skip if trade already open
            if open_trade is not None:
                equity_curve.append(balance)
                continue

            # Generate signal on slice up to current bar
            signal = self.strategy.generate_signal(df.iloc[: i + 1])
            if signal is None:
                equity_curve.append(balance)
                continue

            # Position sizing (simplified fixed % risk)
            risk_pct = self.settings.get("risk_per_trade_pct", 1.0) / 100
            risk_amount = balance * risk_pct
            sl_distance = abs(row["close"] - signal["stop_loss"])
            pip_value = 10.0  # per lot XAUUSD
            lot_size = risk_amount / (sl_distance * pip_value * 100) if sl_distance > 0 else 0.01
            lot_size = min(max(round(lot_size, 2), 0.01), self.settings.get("max_lot_size", 1.0))

            open_trade = {
                "direction": signal["direction"],
                "entry_price": row["close"],
                "entry_time": row["time"],
                "stop_loss": signal["stop_loss"],
                "take_profit": signal["take_profit"],
                "lot_size": lot_size,
                "strategy": signal["strategy"],
                "signal_strength": signal["signal_strength"],
            }

            equity_curve.append(balance)

        # Close any remaining open trade at end
        if open_trade is not None:
            last_price = df.iloc[-1]["close"]
            if open_trade["direction"] == "BUY":
                pnl = (last_price - open_trade["entry_price"]) * open_trade["lot_size"] * 100
            else:
                pnl = (open_trade["entry_price"] - last_price) * open_trade["lot_size"] * 100
            balance += pnl
            open_trade["exit_price"] = last_price
            open_trade["exit_time"] = df.iloc[-1]["time"]
            open_trade["pnl"] = pnl
            open_trade["status"] = "force_closed"
            trades.append(open_trade)
            equity_curve.append(balance)

        return self._calculate_metrics(trades, equity_curve, initial_balance)

    def _check_trade_close(self, trade: dict, row: pd.Series):
        """Check if trade hits SL or TP."""
        if trade["direction"] == "BUY":
            if row["low"] <= trade["stop_loss"]:
                pnl = (trade["stop_loss"] - trade["entry_price"]) * trade["lot_size"] * 100
                return True, pnl
            if row["high"] >= trade["take_profit"]:
                pnl = (trade["take_profit"] - trade["entry_price"]) * trade["lot_size"] * 100
                return True, pnl
        else:
            if row["high"] >= trade["stop_loss"]:
                pnl = (trade["entry_price"] - trade["stop_loss"]) * trade["lot_size"] * 100
                return True, pnl
            if row["low"] <= trade["take_profit"]:
                pnl = (trade["entry_price"] - trade["take_profit"]) * trade["lot_size"] * 100
                return True, pnl
        return False, 0

    def _calculate_metrics(self, trades: List[dict], equity_curve: List[float], initial_balance: float) -> dict:
        """Compute comprehensive performance statistics."""
        if not trades:
            return {"error": "No trades generated"}

        trades_df = pd.DataFrame(trades)
        pnl_series = trades_df["pnl"]
        wins = pnl_series[pnl_series > 0]
        losses = pnl_series[pnl_series <= 0]

        total_pnl = pnl_series.sum()
        final_balance = initial_balance + total_pnl
        win_rate = len(wins) / len(trades_df) * 100 if len(trades_df) > 0 else 0

        # Drawdown
        equity = pd.Series(equity_curve)
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()

        # Profit factor
        gross_profit = wins.sum() if len(wins) > 0 else 0
        gross_loss = abs(losses.sum()) if len(losses) > 0 else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Sharpe ratio (simplified)
        daily_returns = pd.Series(equity_curve).pct_change().dropna()
        sharpe = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0

        return {
            "summary": {
                "initial_balance": initial_balance,
                "final_balance": round(final_balance, 2),
                "total_pnl": round(total_pnl, 2),
                "total_return_pct": round((final_balance / initial_balance - 1) * 100, 2),
                "total_trades": len(trades_df),
                "win_rate_pct": round(win_rate, 2),
                "profit_factor": round(profit_factor, 3),
                "max_drawdown_pct": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe, 3),
                "avg_win": round(wins.mean(), 2) if len(wins) > 0 else 0,
                "avg_loss": round(losses.mean(), 2) if len(losses) > 0 else 0,
                "best_trade": round(pnl_series.max(), 2),
                "worst_trade": round(pnl_series.min(), 2),
            },
            "equity_curve": equity_curve,
            "trades": trades_df.to_dict("records"),
        }
