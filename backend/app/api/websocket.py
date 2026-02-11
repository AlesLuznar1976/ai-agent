from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    """Upravlja WebSocket povezave"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Nova povezava"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        print(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Prekinjena povezava"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f"User {user_id} disconnected")

    async def send_to_user(self, user_id: str, message: dict):
        """Pošlji sporočilo uporabniku (vse naprave)"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        """Pošlji vsem povezanim uporabnikom"""
        for user_id in self.active_connections:
            await self.send_to_user(user_id, message)

    def get_connected_users(self) -> list[str]:
        """Vrne seznam povezanih uporabnikov"""
        return list(self.active_connections.keys())


manager = ConnectionManager()


@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint za real-time obvestila"""

    await manager.connect(websocket, user_id)

    # Pošlji dobrodošlico
    await websocket.send_json({
        "type": "connected",
        "message": "Povezava vzpostavljena",
        "timestamp": datetime.now().isoformat()
    })

    try:
        while True:
            # Prejmi sporočilo (za heartbeat)
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Lahko procesiramo tudi druge ukaze
                try:
                    message = json.loads(data)
                    # Procesiraj sporočilo če je potrebno
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# Helper funkcije za pošiljanje obvestil

async def notify_user(user_id: str, notification_type: str, title: str, message: str, **kwargs):
    """Pošlji obvestilo uporabniku"""
    await manager.send_to_user(user_id, {
        "type": notification_type,
        "title": title,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    })


async def notify_new_email(user_id: str, email_data: dict):
    """Obvestilo o novem emailu"""
    await notify_user(
        user_id,
        "new_email",
        "Nov email",
        f"Od: {email_data.get('sender')} - {email_data.get('subject')}",
        email_id=email_data.get('id'),
        kategorija=email_data.get('kategorija')
    )


async def notify_project_update(user_id: str, projekt_id: int, message: str):
    """Obvestilo o spremembi projekta"""
    await notify_user(
        user_id,
        "project_update",
        "Sprememba projekta",
        message,
        projekt_id=projekt_id
    )


async def notify_action_pending(user_id: str, action_id: str, description: str):
    """Obvestilo o čakajoči akciji"""
    await notify_user(
        user_id,
        "action_pending",
        "Čaka potrditev",
        description,
        action_id=action_id,
        action_required=True
    )
