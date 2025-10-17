"""Pydantic response models."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ChatResponse(BaseModel):
    """Chat endpoint response."""

    session_id: str
    mode: str
    response: str
    timestamp: str
    sql: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class QueryExecutionResponse(BaseModel):
    """Query execution response."""

    success: bool
    query_type: str
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    rows_affected: Optional[int] = None
    columns: Optional[List[str]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
