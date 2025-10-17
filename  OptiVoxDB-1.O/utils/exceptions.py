"""Custom exception classes for OptiVox DB."""

from typing import Optional, Dict, Any


class OptiVoxException(Exception):
    """Base exception for OptiVox DB."""

    def __init__(
            self,
            message: str,
            error_code: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "OPTIVOX_ERROR"
        self.details = details or {}


class DatabaseConnectionError(OptiVoxException):
    """Database connection failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DB_CONNECTION_ERROR", details)


class QueryExecutionError(OptiVoxException):
    """Query execution failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "QUERY_EXECUTION_ERROR", details)


class QueryTimeoutError(OptiVoxException):
    """Query execution timeout."""

    def __init__(self, message: str, timeout: int):
        super().__init__(
            message,
            "QUERY_TIMEOUT",
            {"timeout_seconds": timeout}
        )


class UnsafeQueryError(OptiVoxException):
    """Query blocked for safety reasons."""

    def __init__(self, message: str, reason: str, sql: str):
        super().__init__(
            message,
            "UNSAFE_QUERY",
            {"reason": reason, "sql": sql}
        )


class AIServiceError(OptiVoxException):
    """AI service unavailable or failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AI_SERVICE_ERROR", details)


class SessionNotFoundError(OptiVoxException):
    """Session not found."""

    def __init__(self, session_id: str):
        super().__init__(
            f"Session {session_id} not found",
            "SESSION_NOT_FOUND",
            {"session_id": session_id}
        )
