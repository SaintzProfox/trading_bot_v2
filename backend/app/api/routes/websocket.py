"""
WebSocket Routes - Real-time trading updates
"""
import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
import os

logger = logging.getLogger(__name__)
router = APIRouter()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"


class ConnectionManager:
    """Manages WebSocket connections for broadcasting."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f"WS connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        logger.info(f"WS disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

    async def send_to(self, ws: WebSocket, data: dict):
        await ws.send_text(json.dumps(data))


manager = ConnectionManager()


@router.websocket("/trading")
async def trading_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Real-time trading updates WebSocket.
    Broadcasts: trade_opened, trade_closed, bot_status, account_update
    """
    # Authenticate
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket)

    try:
        # Send initial connection message
        await manager.send_to(websocket, {
            "type": "connected",
            "message": f"Connected as {username}",
        })

        # Keep alive with periodic pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await manager.send_to(websocket, {"type": "pong"})
            except asyncio.TimeoutError:
                await manager.send_to(websocket, {"type": "ping"})
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


async def broadcast_trade_event(event_type: str, data: dict):
    """Called internally when trades are opened/closed."""
    await manager.broadcast({"type": event_type, "data": data})


async def broadcast_bot_status(status: str, account: dict = None):
    """Broadcast bot status change."""
    await manager.broadcast({
        "type": "bot_status",
        "status": status,
        "account": account or {},
    })
