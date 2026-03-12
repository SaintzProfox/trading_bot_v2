"""
FastAPI Backend - XAUUSD Trading Bot API
Real-time WebSocket + REST endpoints
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import auth, bot, trades, metrics, settings as settings_router, websocket
from app.services.database import DatabaseService
from app.core.trading_bot import TradingBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global state
db_service: DatabaseService = None
trading_bot: TradingBot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    global db_service, trading_bot

    # Initialize database
    db_service = DatabaseService(os.getenv("DATABASE_URL"))
    await db_service.connect()
    await db_service.run_migrations()
    logger.info("Database connected and migrations applied")

    # Create bot instance (not started yet)
    bot_settings = await db_service.get_strategy_settings()
    trading_bot = TradingBot(settings=bot_settings, db=db_service)

    # Inject into app state
    app.state.db = db_service
    app.state.bot = trading_bot

    logger.info("Trading Bot API ready")
    yield

    # Cleanup
    if trading_bot and trading_bot.is_running:
        await trading_bot.stop()
    if db_service:
        await db_service.disconnect()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="XAUUSD Trading Bot API",
        description="Production trading bot for HFM broker - XAUUSD",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(bot.router, prefix="/api/bot", tags=["Bot Control"])
    app.include_router(trades.router, prefix="/api/trades", tags=["Trades"])
    app.include_router(metrics.router, prefix="/api/metrics", tags=["Performance"])
    app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
    app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "service": "trading-bot-api"}

    return app


app = create_app()
