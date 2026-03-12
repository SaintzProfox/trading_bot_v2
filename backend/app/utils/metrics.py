"""
Metrics Calculator - Performance statistics
"""
from typing import List
import pandas as pd
import numpy as np


class MetricsCalculator:
    def compute_summary(self, trades: List[dict]) -> dict:
        if not trades:
            return self._empty_summary()

        df = pd.DataFrame(trades)
        pnl = df["pnl"].fillna(0)
        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]

        total_pnl = float(pnl.sum())
        win_rate = len(wins) / len(df) * 100 if len(df) > 0 else 0
        profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) > 0 and losses.sum() != 0 else 0

        equity = pnl.cumsum()
        rolling_max = equity.cummax()
        drawdown = equity - rolling_max
        max_dd = float(drawdown.min())

        return {
            "total_trades": len(df),
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 3),
            "max_drawdown": round(max_dd, 2),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "avg_win": round(float(wins.mean()), 2) if len(wins) > 0 else 0,
            "avg_loss": round(float(losses.mean()), 2) if len(losses) > 0 else 0,
            "best_trade": round(float(pnl.max()), 2),
            "worst_trade": round(float(pnl.min()), 2),
            "total_profit": round(float(wins.sum()), 2),
            "total_loss": round(float(losses.sum()), 2),
        }

    def build_equity_curve(self, trades: List[dict]) -> List[dict]:
        if not trades:
            return []
        df = pd.DataFrame(trades).sort_values("closed_at")
        df["cumulative_pnl"] = df["pnl"].fillna(0).cumsum()
        return [
            {
                "date": str(row["closed_at"])[:10],
                "equity": round(10000 + row["cumulative_pnl"], 2),
                "pnl": round(row["pnl"] or 0, 2),
            }
            for _, row in df.iterrows()
        ]

    def compute_drawdown(self, trades: List[dict]) -> dict:
        if not trades:
            return {"max_drawdown": 0, "data": []}
        df = pd.DataFrame(trades).sort_values("closed_at")
        equity = 10000 + df["pnl"].fillna(0).cumsum()
        rolling_max = equity.cummax()
        dd = equity - rolling_max
        return {
            "max_drawdown": round(float(dd.min()), 2),
            "max_drawdown_pct": round(float((dd / rolling_max).min() * 100), 2),
            "data": [
                {"date": str(df.iloc[i]["closed_at"])[:10], "drawdown": round(float(dd.iloc[i]), 2)}
                for i in range(len(dd))
            ],
        }

    def _empty_summary(self) -> dict:
        return {
            "total_trades": 0, "total_pnl": 0, "win_rate": 0,
            "profit_factor": 0, "max_drawdown": 0, "winning_trades": 0,
            "losing_trades": 0, "avg_win": 0, "avg_loss": 0,
            "best_trade": 0, "worst_trade": 0, "total_profit": 0, "total_loss": 0,
        }
