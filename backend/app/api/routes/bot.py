"""
API Routes - Bot Control
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.deps import get_current_user, get_bot, get_db
from app.services.database import DatabaseService
from app.core.trading_bot import TradingBot

router = APIRouter()


@router.post("/start")
async def start_bot(
    request: Request,
    current_user=Depends(get_current_user),
    bot: TradingBot = Depends(get_bot),
    db: DatabaseService = Depends(get_db),
):
    if bot.is_running:
        raise HTTPException(status_code=400, detail="Bot already running")
    try:
        # Reload settings before starting
        settings = await db.get_strategy_settings()
        bot.settings = settings
        bot.strategy.settings = settings
        bot.risk_manager.settings = settings
        await bot.start()
        return {"status": "started", "message": "Trading bot started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_bot(
    current_user=Depends(get_current_user),
    bot: TradingBot = Depends(get_bot),
):
    if not bot.is_running:
        raise HTTPException(status_code=400, detail="Bot is not running")
    await bot.stop()
    return {"status": "stopped", "message": "Trading bot stopped"}


@router.post("/emergency-stop")
async def emergency_stop(
    current_user=Depends(get_current_user),
    bot: TradingBot = Depends(get_bot),
):
    """Stop bot and close all open positions."""
    await bot.close_all_positions()
    await bot.stop()
    return {"status": "emergency_stopped", "message": "All positions closed, bot stopped"}


@router.get("/status")
async def get_status(
    current_user=Depends(get_current_user),
    bot: TradingBot = Depends(get_bot),
    db: DatabaseService = Depends(get_db),
):
    account_info = await bot.get_account_info() if bot.is_connected else {}
    db_status = await db.get_bot_status()
    return {
        "is_running": bot.is_running,
        "is_connected": bot.is_connected,
        "status": db_status,
        "account": account_info,
    }
