"""Pydantic request models."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ConnectionModel(BaseModel):
    """Database connection parameters."""

    user: str
    password: str
    host: str
    database: str
    port: Optional[int] = 3306

    @field_validator("host")
    @classmethod
    def host_not_empty(cls, v: str) -> str:
        """Validate host is not empty."""
        if not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """Primary chat interface request."""

    message: str = Field(..., description="Your question or instruction")
    connection: ConnectionModel
    session_id: Optional[str] = None
    mode: Optional[str] = Field(default="assistant")
    allow_destructive: bool = False
    confirm: bool = False
    stream: bool = Field(default=False, description="Stream response in real-time")


class NaturalQueryRequest(BaseModel):
    """Natural language query request."""

    prompt: str = Field(..., description="Natural language instruction")
    connection: ConnectionModel
    mode: Optional[str] = Field(default="query")
    session_id: Optional[str] = None
    allow_destructive: bool = False
    confirm: bool = False
    simulate_only: bool = False


class ExplanationRequest(BaseModel):
    """Educational explanation request."""

    topic: str
    difficulty: str = "Beginner"
    include_examples: bool = True
    include_exercises: bool = True
    connection: Optional[ConnectionModel] = None


class OptimizationRequest(BaseModel):
    """Query optimization request."""

    connection: ConnectionModel
    sql: str
    analyze_indexes: bool = True
    suggest_rewrites: bool = True


class SchemaAnalysisRequest(BaseModel):
    """Schema analysis request."""

    connection: ConnectionModel
    include_recommendations: bool = True
    analyze_relationships: bool = True


class DebugRequest(BaseModel):
    """Debug request."""

    sql: str
    error_message: Optional[str] = None
    connection: Optional[ConnectionModel] = None
