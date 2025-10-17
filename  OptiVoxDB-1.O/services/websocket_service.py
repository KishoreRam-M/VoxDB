"""WebSocket connection management."""

from typing import Dict, Any
from fastapi import WebSocket

from Core.Logging import logger


class WebSocketManager:
    """Manage WebSocket connections for real-time streaming."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """
        Accept and register WebSocket connection.

        Args:
            session_id: Session identifier
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str) -> None:
        """
        Remove WebSocket connection.

        Args:
            session_id: Session identifier
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(
            self,
            session_id: str,
            message: Dict[str, Any]
    ) -> None:
        """
        Send message to WebSocket client.

        Args:
            session_id: Session identifier
            message: Message dictionary to send
        """
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                self.disconnect(session_id)

    async def send_text(
            self,
            session_id: str,
            text: str
    ) -> None:
        """
        Send text message to WebSocket client.

        Args:
            session_id: Session identifier
            text: Text message
        """
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(text)
            except Exception as e:
                logger.error(f"Failed to send WebSocket text: {e}")
                self.disconnect(session_id)

    def is_connected(self, session_id: str) -> bool:
        """Check if session has active WebSocket connection."""
        return session_id in self.active_connections

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
