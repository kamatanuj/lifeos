"""WebSocket for voice agent → frontend screen navigation"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from datetime import datetime

router = APIRouter()

# Store active WebSocket connections
active_connections: list[WebSocket] = []

# Latest navigation command issued by the voice agent (polling fallback).
# A page only auto-navigates to this when the command is NEWER than the moment
# the page itself loaded — otherwise a fresh open of the app would instantly be
# yanked off the default Dashboard to whatever screen some earlier voice session
# (possibly hours ago) last touched. The page sends its load time on connect /
# in the poll query, and only commands newer than that are ever delivered.
latest_nav: dict = {"action": "none", "screen": "dashboard", "timestamp": "", "data": {}}


@router.websocket("/api/voice/ws")
async def voice_ws(websocket: WebSocket):
    """Voice-nav WebSocket. The page appends ?since=<ISO timestamp> (its own
    load time); only commands newer than that are replayed on connect."""
    await websocket.accept()
    # 'since' = page load time. Commands at/before it are history, not live.
    since = websocket.query_params.get("since", "") or ""
    active_connections.append(websocket)
    try:
        # Replay the latest nav on connect ONLY if it is newer than the page.
        if (latest_nav.get("action") == "navigate" and latest_nav.get("timestamp")
                and (not since or latest_nav["timestamp"] > since)):
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
def nav_status(since: str = Query("")):
    """Polling fallback: get the latest navigation command.

    The page passes 'since' = the timestamp the page loaded (ISO). A command
    at/before that moment is history from a previous session and is suppressed,
    so a fresh page open always lands on the default Dashboard.
    """
    nav = latest_nav
    if since and nav.get("timestamp") and nav["timestamp"] <= since:
        nav = {**nav, "action": "none"}
    return nav