"""
XAUUSD Trading Bot - Core Engine
HFM Broker | MetaTrader5 Integration
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from app.core.strategy import TradingStrategy
from app.core.risk_manager import RiskManager
from app.models.trade import TradeModel
from app.models.bot_status import BotStatusModel
from app.services.database import DatabaseService
from app.utils.metrics import MetricsCalculator

logger = logging.getLogger(__name__)


class TradingBot:
    """Production-grade XAUUSD trading bot for HFM broker."""

    SYMBOL = "XAUUSD"
    MAGIC_NUMBER = 20240101

    def __init__(self, settings: dict, db: DatabaseService):
        self.settings = settings
        self.db = db
        self.strategy = TradingStrategy(settings)
        self.risk_manager = RiskManager(settings)
        self.metrics = MetricsCalculator()
        self.is_running = False
        self.is_connected = False
        self._task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Initialize MT5 connection to HFM broker."""
        if not mt5.initialize(
            login=int(self.settings["mt5_login"]),
            password=self.settings["mt5_password"],
            server=self.settings["mt5_server"],
        ):
            logger.error(f"MT5 init failed: {mt5.last_error()}")
            return False

        account = mt5.account_info()
        if account is None:
            logger.error("Failed to get account info")
            mt5.shutdown()
            return False

        logger.info(f"Connected: {account.login} | Balance: {account.balance}")
        self.is_connected = True

        # Ensure XAUUSD is visible
        mt5.symbol_select(self.SYMBOL, True)
        return True

    async def disconnect(self):
        """Safely disconnect from MT5."""
        mt5.shutdown()
        self.is_connected = False
        logger.info("Disconnected from MT5")

    async def start(self):
        """Start the trading bot main loop."""
        if self.is_running:
            logger.warning("Bot already running")
            return

        connected = await self.connect()
        if not connected:
            raise ConnectionError("Failed to connect to MT5/HFM")

        self.is_running = True
        await self.db.update_bot_status("running")
        logger.info("Trading bot started")

        self._task = asyncio.create_task(self._main_loop())

    async def stop(self):
        """Stop the trading bot gracefully."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self.disconnect()
        await self.db.update_bot_status("stopped")
        logger.info("Trading bot stopped")

    async def _main_loop(self):
        """Main trading loop."""
        while self.is_running:
            try:
                await self._trading_cycle()
                interval = self.settings.get("check_interval_seconds", 60)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _trading_cycle(self):
        """Execute one trading cycle: analyze + execute."""
        # Check daily loss limit
        if await self.risk_manager.daily_loss_exceeded(self.db):
            logger.warning("Daily loss limit reached, skipping cycle")
            return

        # Check max open trades
        open_trades = self._get_open_positions()
        max_trades = self.settings.get("max_open_trades", 3)
        if len(open_trades) >= max_trades:
            logger.info(f"Max open trades ({max_trades}) reached")
            return

        # Fetch candles
        timeframe = self._get_timeframe()
        rates = mt5.copy_rates_from_pos(self.SYMBOL, timeframe, 0, 200)
        if rates is None or len(rates) < 50:
            logger.warning("Insufficient price data")
            return

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")

        # Generate signal
        signal = self.strategy.generate_signal(df)
        if signal is None:
            return

        # Calculate position size
        account = mt5.account_info()
        if account is None:
            return

        lot_size = self.risk_manager.calculate_lot_size(
            balance=account.balance,
            symbol_info=mt5.symbol_info(self.SYMBOL),
            signal=signal,
        )
        if lot_size <= 0:
            return

        # Execute trade
        await self._execute_trade(signal, lot_size)

    def _get_open_positions(self) -> list:
        positions = mt5.positions_get(symbol=self.SYMBOL, magic=self.MAGIC_NUMBER)
        return list(positions) if positions else []

    def _get_timeframe(self) -> int:
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        return tf_map.get(self.settings.get("timeframe", "H1"), mt5.TIMEFRAME_H1)

    async def _execute_trade(self, signal: dict, lot_size: float):
        """Execute a trade order on MT5."""
        tick = mt5.symbol_info_tick(self.SYMBOL)
        if tick is None:
            logger.error("Failed to get tick data")
            return

        sl = signal["stop_loss"]
        tp = signal["take_profit"]
        order_type = mt5.ORDER_TYPE_BUY if signal["direction"] == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if signal["direction"] == "BUY" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.SYMBOL,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": self.MAGIC_NUMBER,
            "comment": f"Bot|{signal['strategy']}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return

        logger.info(f"Order executed: {signal['direction']} {lot_size} lots @ {price}")

        # Save to DB
        await self.db.save_trade({
            "ticket": result.order,
            "symbol": self.SYMBOL,
            "direction": signal["direction"],
            "lot_size": lot_size,
            "entry_price": price,
            "stop_loss": sl,
            "take_profit": tp,
            "strategy": signal["strategy"],
            "status": "open",
            "opened_at": datetime.utcnow(),
        })

    async def get_account_info(self) -> dict:
        """Return current account metrics."""
        if not self.is_connected:
            return {}
        account = mt5.account_info()
        if account is None:
            return {}
        return {
            "balance": account.balance,
            "equity": account.equity,
            "margin": account.margin,
            "free_margin": account.margin_free,
            "profit": account.profit,
            "currency": account.currency,
        }

    async def close_all_positions(self):
        """Emergency: close all open positions."""
        positions = self._get_open_positions()
        for pos in positions:
            tick = mt5.symbol_info_tick(self.SYMBOL)
            close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.SYMBOL,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": close_price,
                "deviation": 20,
                "magic": self.MAGIC_NUMBER,
                "comment": "Bot|EmergencyClose",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Closed position {pos.ticket}")
