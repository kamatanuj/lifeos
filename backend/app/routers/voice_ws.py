"""WebSocket for voice agent → frontend screen navigation"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

router = APIRouter()

# Store active WebSocket connections
active_connections: list[WebSocket] = []

# Store the latest navigation command (for polling fallback)
latest_nav: dict = {"action": "none", "screen": "dashboard", "timestamp": "", "data": {}}


@router.websocket("/api/voice/ws")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send the latest nav on connect
        await websocket.send_text(json.dumps(latest_nav))
        while True:
            await asyncio.sleep(30)  # keep alive
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)


def push_navigation(screen: str, action: str = "navigate", data: dict = None):
    """Push a navigation command to all connected WebSocket clients"""
    global latest_nav
    latest_nav = {
        "action": action,
        "screen": screen,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
    }
    for conn in list(active_connections):
        try:
            asyncio.create_task(conn.send_text(json.dumps(latest_nav)))
        except Exception:
            if conn in active_connections:
                active_connections.remove(conn)


@router.get("/api/voice/nav-status")
def nav_status():
    """Polling fallback: get the latest navigation command"""
    return latest_nav