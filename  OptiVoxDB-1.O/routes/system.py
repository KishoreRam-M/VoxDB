"""System health and information endpoints."""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from Core.Config import settings
from Core.Logging import logger

#from models.responses import StandardResponse
import models.response
from services.ai_service import ai_service
from services.session_service import session_service
from services.websocket_service import ws_manager

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/")
async def root():
    """Root endpoint - welcome message."""
    return {
        "service": "OptiVox DB",
        "version": "2.0.0",
        "status": "operational",
        "description": "Advanced AI-powered database assistant",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status with service availability
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ai": ai_service.is_available(),
            "database": True
        },
        "connections": {
            "websockets": ws_manager.get_connection_count(),
            "sessions": len(session_service.get_all_sessions())
        }
    }


@router.get("/info")
async def system_info():
    """
    Get system information and configuration.

    Returns:
        System configuration details
    """
    return StandardResponse(
        success=True,
        data={
            "environment": settings.environment.value,
            "debug": settings.debug,
            "ai_model": settings.default_model,
            "features": {
                "ai_enabled": ai_service.is_available(),
                "streaming": True,
                "optimization": True,
                "teaching_mode": True,
                "debug_mode": True
            },
            "limits": {
                "max_query_time": settings.max_query_execution_time,
                "max_chat_history": settings.max_chat_history,
                "session_timeout": settings.session_timeout_minutes
            }
        }
    )


@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions.

    Returns:
        List of active session summaries
    """
    sessions = session_service.get_all_sessions()

    return StandardResponse(
        success=True,
        data={
            "total": len(sessions),
            "sessions": sessions
        }
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a specific session.

    Args:
        session_id: Session identifier

    Returns:
        Deletion status
    """
    deleted = session_service.delete(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return StandardResponse(
        success=True,
        data={"message": f"Session {session_id} deleted"}
    )


@router.post("/cleanup")
async def cleanup_expired_sessions():
    """
    Clean up expired sessions.

    Returns:
        Number of sessions cleaned up
    """
    count = session_service.cleanup_expired()

    return StandardResponse(
        success=True,
        data={
            "message": f"Cleaned up {count} expired sessions",
            "count": count
        }
    )
