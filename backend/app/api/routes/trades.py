"""
Trades Routes
"""
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user, get_db
from app.services.database import DatabaseService

router = APIRouter()


@router.get("/")
async def get_trades(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: str = Query(None),
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    offset = (page - 1) * limit
    trades = await db.get_trades(limit=limit, offset=offset, status=status)
    total = await db.count_trades(status=status)
    return {"trades": trades, "total": total, "page": page, "limit": limit}


@router.get("/open")
async def get_open_trades(
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    trades = await db.get_trades(status="open", limit=100)
    return {"trades": trades}


@router.get("/{trade_id}")
async def get_trade(
    trade_id: int,
    current_user=Depends(get_current_user),
    db: DatabaseService = Depends(get_db),
):
    trade = await db.get_trade_by_id(trade_id)
    if not trade:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade
