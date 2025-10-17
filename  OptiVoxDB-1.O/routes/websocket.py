"""WebSocket endpoints for real-time streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

from Core.Logging import logger
from services.websocket_service import ws_manager
from services.chat_service import chat_service
from models.domain import OperationMode

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat streaming.

    Args:
        websocket: WebSocket connection
        session_id: Session identifier
    """
    await ws_manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message = data.get("message")
            connection = data.get("connection")
            mode = data.get("mode", "assistant")

            if not message or not connection:
                await ws_manager.send_message(
                    session_id,
                    {
                        "type": "error",
                        "message": "Missing required fields"
                    }
                )
                continue

            try:
                # Process chat message
                mode_enum = OperationMode(mode)
            except ValueError:
                mode_enum = OperationMode.ASSISTANT

            # Send processing status
            await ws_manager.send_message(
                session_id,
                {
                    "type": "status",
                    "message": "Processing your request..."
                }
            )

            # Process and send response
            try:
                result = await chat_service.process_chat_message(
                    message=message,
                    connection=connection,
                    session_id=session_id,
                    mode=mode_enum,
                    allow_destructive=data.get("allow_destructive", False),
                    confirm=data.get("confirm", False)
                )

                await ws_manager.send_message(
                    session_id,
                    {
                        "type": "response",
                        "data": result
                    }
                )

            except Exception as e:
                logger.error(f"WebSocket processing error: {e}")
                await ws_manager.send_message(
                    session_id,
                    {
                        "type": "error",
                        "message": str(e)
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        ws_manager.disconnect(session_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        ws_manager.disconnect(session_id)
