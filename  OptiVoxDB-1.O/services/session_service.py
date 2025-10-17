"""Session management service."""

from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from models.domain import SessionContext, ChatMessage
from Core.Config import settings
from Core.Logging import logger
from utils.exceptions import SessionNotFoundError


class SessionService:
    """Manage user sessions and chat histories."""

    def __init__(self):
        """Initialize session service."""
        self._sessions: Dict[str, SessionContext] = {}
        self._chat_histories: Dict[str, list[ChatMessage]] = defaultdict(list)

    def get_or_create(self, session_id: Optional[str] = None) -> SessionContext:
        """
        Get existing session or create new one.

        Args:
            session_id: Optional session ID

        Returns:
            SessionContext instance
        """
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.last_activity = datetime.utcnow()
            return session

        # Create new session
        new_id = session_id or f"session_{datetime.utcnow().timestamp()}"
        new_session = SessionContext(session_id=new_id)
        self._sessions[new_id] = new_session

        logger.info(f"Session created: {new_id}")
        return new_session

    def get(self, session_id: str) -> SessionContext:
        """
        Get existing session.

        Args:
            session_id: Session ID

        Returns:
            SessionContext instance

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)

        session = self._sessions[session_id]
        session.last_activity = datetime.utcnow()
        return session

    def update_context(
            self,
            session: SessionContext,
            query: str,
            result: Dict
    ) -> None:
        """
        Update session context with query result.

        Args:
            session: SessionContext instance
            query: Executed query
            result: Query result
        """
        session.last_query = query
        session.last_result = result
        session.conversation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "result": result
        })

        # Limit history size
        if len(session.conversation_history) > 10:
            session.conversation_history = session.conversation_history[-10:]

        session.last_activity = datetime.utcnow()

    def add_message(
            self,
            session_id: str,
            role: str,
            content: str,
            metadata: Optional[Dict] = None
    ) -> None:
        """
        Add message to chat history.

        Args:
            session_id: Session ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata
        """
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        self._chat_histories[session_id].append(message)

        # Limit chat history
        max_history = settings.max_chat_history
        if len(self._chat_histories[session_id]) > max_history:
            self._chat_histories[session_id] = \
                self._chat_histories[session_id][-max_history:]

        logger.debug(f"Message added to session {session_id}")

    def get_chat_history(self, session_id: str) -> list[Dict]:
        """
        Get chat history for session.

        Args:
            session_id: Session ID

        Returns:
            List of chat messages as dictionaries
        """
        return [msg.to_dict() for msg in self._chat_histories[session_id]]

    def delete(self, session_id: str) -> bool:
        """
        Delete session and its history.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        deleted = False

        if session_id in self._sessions:
            del self._sessions[session_id]
            deleted = True

        if session_id in self._chat_histories:
            del self._chat_histories[session_id]
            deleted = True

        if deleted:
            logger.info(f"Session deleted: {session_id}")

        return deleted

    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        timeout = timedelta(minutes=settings.session_timeout_minutes)
        cutoff = datetime.utcnow() - timeout

        expired = [
            sid for sid, session in self._sessions.items()
            if session.last_activity < cutoff
        ]

        for session_id in expired:
            self.delete(session_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    def get_all_sessions(self) -> list[Dict]:
        """
        Get all active sessions.

        Returns:
            List of session summaries
        """
        return [
            {
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "message_count": len(self._chat_histories[session.session_id])
            }
            for session in self._sessions.values()
        ]


# Global session service instance
session_service = SessionService()
