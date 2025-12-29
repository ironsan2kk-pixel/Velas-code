"""
VELAS API - WebSocket Routes

Real-time updates для фронтенда.
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Менеджер WebSocket соединений."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Принять новое соединение."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = {"signals", "positions", "system"}
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Отключить соединение."""
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Отправить сообщение конкретному клиенту."""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: Dict[str, Any], channel: str = None):
        """Отправить сообщение всем подключенным клиентам."""
        disconnected = []
        
        for websocket in self.active_connections:
            if channel and channel not in self.subscriptions.get(websocket, set()):
                continue
            
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()


async def heartbeat(websocket: WebSocket):
    """Отправка heartbeat для поддержания соединения."""
    while True:
        try:
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
            })
            await asyncio.sleep(30)
        except Exception:
            break


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint для real-time обновлений."""
    
    await manager.connect(websocket)
    
    await manager.send_personal(websocket, {
        "type": "connected",
        "message": "Connected to VELAS WebSocket",
        "timestamp": datetime.utcnow().isoformat(),
        "channels": ["signals", "positions", "system"],
    })
    
    heartbeat_task = asyncio.create_task(heartbeat(websocket))
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type", "")
                
                if msg_type == "subscribe":
                    channels = message.get("channels", [])
                    if websocket in manager.subscriptions:
                        manager.subscriptions[websocket].update(channels)
                    await manager.send_personal(websocket, {
                        "type": "subscribed",
                        "channels": channels,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                
                elif msg_type == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": "Invalid JSON",
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        heartbeat_task.cancel()
        manager.disconnect(websocket)


def get_manager() -> ConnectionManager:
    return manager
