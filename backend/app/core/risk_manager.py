"""
Risk Management Module
Max risk per trade, daily loss limit, position sizing
"""
import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Enforces risk rules:
    - Max % risk per trade
    - Daily loss limit
    - Max open trades
    - Position sizing via fixed fractional method
    """

    def __init__(self, settings: dict):
        self.settings = settings

    def calculate_lot_size(
        self,
        balance: float,
        symbol_info,
        signal: dict,
    ) -> float:
        """
        Calculate position size based on risk % and SL distance.
        Returns lot size rounded to broker's step.
        """
        risk_pct = self.settings.get("risk_per_trade_pct", 1.0) / 100
        risk_amount = balance * risk_pct

        price = signal.get("entry_price", 0)
        sl = signal["stop_loss"]
        direction = signal["direction"]

        if direction == "BUY":
            sl_pips = abs(price - sl) if price > 0 else self.settings.get("default_sl_pips", 150)
        else:
            sl_pips = abs(sl - price) if price > 0 else self.settings.get("default_sl_pips", 150)

        if sl_pips == 0:
            logger.warning("SL distance is zero, using default")
            sl_pips = 150

        # XAUUSD: 1 pip = $0.01, 1 lot = 100 oz
        # Pip value per lot for XAUUSD ≈ $10 (at ~$2000/oz)
        pip_value_per_lot = 10.0  # Approximate for XAUUSD

        raw_lots = risk_amount / (sl_pips * pip_value_per_lot)

        # Apply broker constraints
        if symbol_info:
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
        else:
            min_lot, max_lot, lot_step = 0.01, 100.0, 0.01

        # Round to lot step
        lots = round(raw_lots / lot_step) * lot_step
        lots = max(min_lot, min(lots, max_lot))

        # Additional cap: never risk more than max configured lots
        max_configured = self.settings.get("max_lot_size", 1.0)
        lots = min(lots, max_configured)

        logger.info(f"Calculated lot size: {lots} (risk: ${risk_amount:.2f}, SL pips: {sl_pips})")
        return round(lots, 2)

    async def daily_loss_exceeded(self, db) -> bool:
        """Check if daily loss limit has been hit."""
        limit_pct = self.settings.get("daily_loss_limit_pct", 5.0)
        if limit_pct <= 0:
            return False

        today_pnl = await db.get_daily_pnl(date.today())
        account_balance = await db.get_last_balance()

        if account_balance <= 0:
            return False

        loss_pct = abs(min(today_pnl, 0)) / account_balance * 100

        if loss_pct >= limit_pct:
            logger.warning(f"Daily loss limit reached: {loss_pct:.2f}% >= {limit_pct}%")
            return True

        return False

    def validate_signal(self, signal: dict) -> bool:
        """Validate signal meets minimum quality threshold."""
        min_strength = self.settings.get("min_signal_strength", 50)
        return signal.get("signal_strength", 0) >= min_strength
