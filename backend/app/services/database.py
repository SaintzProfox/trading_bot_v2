"""
Database Service - PostgreSQL with asyncpg
"""
import logging
from datetime import date, datetime
from typing import List, Optional
import asyncpg

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.dsn, min_size=2, max_size=10)
        logger.info("Database pool created")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def run_migrations(self):
        """Run SQL migrations to create tables."""
        async with self.pool.acquire() as conn:
            await conn.execute(MIGRATION_SQL)
        logger.info("Migrations applied")

    # --- Users ---

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE username = $1", username
            )
            return dict(row) if row else None

    async def create_user(self, username: str, password_hash: str, email: str) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO users (username, password_hash, email, created_at)
                   VALUES ($1, $2, $3, NOW()) RETURNING *""",
                username, password_hash, email,
            )
            return dict(row)

    # --- Trades ---

    async def save_trade(self, trade: dict) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO trades
                   (ticket, symbol, direction, lot_size, entry_price, stop_loss,
                    take_profit, strategy, status, opened_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   RETURNING *""",
                trade["ticket"], trade["symbol"], trade["direction"],
                trade["lot_size"], trade["entry_price"], trade["stop_loss"],
                trade["take_profit"], trade["strategy"], trade["status"],
                trade["opened_at"],
            )
            return dict(row)

    async def close_trade(self, ticket: int, exit_price: float, pnl: float):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """UPDATE trades SET exit_price = $1, pnl = $2,
                   status = 'closed', closed_at = NOW()
                   WHERE ticket = $3""",
                exit_price, pnl, ticket,
            )

    async def get_trades(
        self, limit: int = 50, offset: int = 0, status: Optional[str] = None
    ) -> List[dict]:
        async with self.pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    "SELECT * FROM trades WHERE status=$1 ORDER BY opened_at DESC LIMIT $2 OFFSET $3",
                    status, limit, offset,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM trades ORDER BY opened_at DESC LIMIT $1 OFFSET $2",
                    limit, offset,
                )
            return [dict(r) for r in rows]

    async def get_trade_by_id(self, trade_id: int) -> Optional[dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM trades WHERE id = $1", trade_id)
            return dict(row) if row else None

    async def get_all_closed_trades(self) -> List[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM trades WHERE status='closed' ORDER BY closed_at"
            )
            return [dict(r) for r in rows]

    async def count_trades(self, status: Optional[str] = None) -> int:
        async with self.pool.acquire() as conn:
            if status:
                return await conn.fetchval("SELECT COUNT(*) FROM trades WHERE status=$1", status)
            return await conn.fetchval("SELECT COUNT(*) FROM trades")

    # --- PnL & Metrics ---

    async def get_daily_pnl(self, day: date) -> float:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                """SELECT COALESCE(SUM(pnl), 0) FROM trades
                   WHERE DATE(closed_at) = $1 AND status='closed'""",
                day,
            )
            return float(result or 0)

    async def get_last_balance(self) -> float:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT balance FROM performance_metrics ORDER BY recorded_at DESC LIMIT 1"
            )
            return float(result or 10000)

    async def get_daily_metrics(self, since: date) -> List[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT
                     DATE(closed_at) as day,
                     COUNT(*) as total_trades,
                     SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                     SUM(pnl) as daily_pnl
                   FROM trades
                   WHERE status='closed' AND DATE(closed_at) >= $1
                   GROUP BY DATE(closed_at)
                   ORDER BY day""",
                since,
            )
            return [dict(r) for r in rows]

    # --- Bot Status ---

    async def get_bot_status(self) -> str:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT status FROM bot_status ORDER BY updated_at DESC LIMIT 1"
            )
            return result or "stopped"

    async def update_bot_status(self, status: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO bot_status (status, updated_at)
                   VALUES ($1, NOW())""",
                status,
            )

    # --- Strategy Settings ---

    async def get_strategy_settings(self) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM strategy_settings ORDER BY updated_at DESC LIMIT 1"
            )
            if row:
                return dict(row)
            return DEFAULT_SETTINGS.copy()

    async def update_strategy_settings(self, settings: dict):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO strategy_settings
                   (timeframe, rsi_period, rsi_oversold, rsi_overbought,
                    fast_ma_period, slow_ma_period, ma_type, atr_period,
                    atr_multiplier_sl, atr_multiplier_tp, risk_per_trade_pct,
                    max_lot_size, daily_loss_limit_pct, max_open_trades,
                    min_signal_strength, use_ml_filter, check_interval_seconds, updated_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,NOW())""",
                settings.get("timeframe", "H1"),
                settings.get("rsi_period", 14),
                settings.get("rsi_oversold", 30),
                settings.get("rsi_overbought", 70),
                settings.get("fast_ma_period", 20),
                settings.get("slow_ma_period", 50),
                settings.get("ma_type", "EMA"),
                settings.get("atr_period", 14),
                settings.get("atr_multiplier_sl", 1.5),
                settings.get("atr_multiplier_tp", 2.5),
                settings.get("risk_per_trade_pct", 1.0),
                settings.get("max_lot_size", 1.0),
                settings.get("daily_loss_limit_pct", 5.0),
                settings.get("max_open_trades", 3),
                settings.get("min_signal_strength", 50),
                settings.get("use_ml_filter", True),
                settings.get("check_interval_seconds", 60),
            )


DEFAULT_SETTINGS = {
    "timeframe": "H1",
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "fast_ma_period": 20,
    "slow_ma_period": 50,
    "ma_type": "EMA",
    "atr_period": 14,
    "atr_multiplier_sl": 1.5,
    "atr_multiplier_tp": 2.5,
    "risk_per_trade_pct": 1.0,
    "max_lot_size": 1.0,
    "daily_loss_limit_pct": 5.0,
    "max_open_trades": 3,
    "min_signal_strength": 50,
    "use_ml_filter": True,
    "check_interval_seconds": 60,
    "mt5_server": "HFM-Demo",
}


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    email VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    ticket BIGINT UNIQUE,
    symbol VARCHAR(20) NOT NULL DEFAULT 'XAUUSD',
    direction VARCHAR(10) NOT NULL,
    lot_size DECIMAL(10,2),
    entry_price DECIMAL(10,4),
    exit_price DECIMAL(10,4),
    stop_loss DECIMAL(10,4),
    take_profit DECIMAL(10,4),
    pnl DECIMAL(12,4),
    strategy VARCHAR(50),
    status VARCHAR(20) DEFAULT 'open',
    opened_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    balance DECIMAL(15,4),
    equity DECIMAL(15,4),
    total_pnl DECIMAL(15,4),
    win_rate DECIMAL(5,2),
    total_trades INT,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS strategy_settings (
    id SERIAL PRIMARY KEY,
    timeframe VARCHAR(10),
    rsi_period INT,
    rsi_oversold INT,
    rsi_overbought INT,
    fast_ma_period INT,
    slow_ma_period INT,
    ma_type VARCHAR(10),
    atr_period INT,
    atr_multiplier_sl DECIMAL(4,2),
    atr_multiplier_tp DECIMAL(4,2),
    risk_per_trade_pct DECIMAL(5,2),
    max_lot_size DECIMAL(10,2),
    daily_loss_limit_pct DECIMAL(5,2),
    max_open_trades INT,
    min_signal_strength INT,
    use_ml_filter BOOLEAN DEFAULT TRUE,
    check_interval_seconds INT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bot_status (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON trades(opened_at);
CREATE INDEX IF NOT EXISTS idx_trades_closed_at ON trades(closed_at);
"""
