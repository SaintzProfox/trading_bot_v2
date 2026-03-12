"""
Strategy Settings Routes
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.api.deps import get_current_user, get_db
from app.services.database import DatabaseService

router = APIRouter()


class StrategySettings(BaseModel):
    timeframe: str = Field("H1", description="Chart timeframe")
    rsi_period: int = Field(14, ge=5, le=50)
    rsi_oversold: int = Field(30, ge=10, le=45)
    rsi_overbought: int = Field(70, ge=55, le=90)
    fast_ma_period: int = Field(20, ge=5, le=100)
    slow_ma_period: int = Field(50, ge=20, le=200)
    ma_type: str = Field("EMA", description="EMA or SMA")
    atr_period: int = Field(14, ge=5, le=30)
    atr_multiplier_sl: float = Field(1.5, ge=0.5, le=5.0)
    atr_multiplier_tp: float = Field(2.5, ge=0.5, le=10.0)
    risk_per_trade_pct: float = Field(1.0, ge=0.1, le=5.0)
    max_lot_size: float = Field(1.0, ge=0.01, le=100.0)
    daily_loss_limit_pct: float = Field(5.0, ge=0.0, le=20.0)
    max_open_trades: int = Field(3, ge=1, le=10)
    min_signal_strength: int = Field(50, ge=0, le=100)
    use_ml_filter: bool = Field(True)
    check_interval_seconds: int = Field(60, ge=10, le=3600)


@router.get("/")
async def get_settings(
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    return await db.get_strategy_settings()


@router.put("/")
async def update_settings(
    settings: StrategySettings,
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    await db.update_strategy_settings(settings.dict())
    return {"message": "Settings updated", "settings": settings.dict()}
