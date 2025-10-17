"""Domain models and data structures."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class OperationMode(str, Enum):
    """OptiVox DB operation modes."""
    QUERY = "query"
    TEACHING = "teaching"
    SIMULATION = "simulation"
    OPTIMIZATION = "optimization"
    INTERVIEW = "interview"
    DEBUG = "debug"
    SEARCH = "search"
    ASSISTANT = "assistant"


class DifficultyLevel(str, Enum):
    """Learning difficulty levels."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


@dataclass
class SessionContext:
    """Real-time session context for multi-turn conversations."""

    session_id: str
    last_query: Optional[str] = None
    last_result: Optional[Dict[str, Any]] = None
    schema_context: Dict[str, Any] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    user_expertise: str = "beginner"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatMessage:
    """Chat message structure."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
