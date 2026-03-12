"""
Performance Metrics Routes
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user, get_db
from app.services.database import DatabaseService
from app.utils.metrics import MetricsCalculator

router = APIRouter()


@router.get("/summary")
async def get_summary(
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    """Overall performance summary."""
    trades = await db.get_all_closed_trades()
    calc = MetricsCalculator()
    return calc.compute_summary(trades)


@router.get("/daily")
async def get_daily_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    """Daily PnL and trade counts."""
    since = date.today() - timedelta(days=days)
    return await db.get_daily_metrics(since=since)


@router.get("/equity-curve")
async def get_equity_curve(
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    """Equity curve data for charting."""
    trades = await db.get_all_closed_trades()
    calc = MetricsCalculator()
    return calc.build_equity_curve(trades)


@router.get("/drawdown")
async def get_drawdown(
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    """Maximum drawdown analysis."""
    trades = await db.get_all_closed_trades()
    calc = MetricsCalculator()
    return calc.compute_drawdown(trades)
