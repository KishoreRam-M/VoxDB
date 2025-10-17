"""Utils module initialization."""

from utils.exceptions import (
    OptiVoxException,
    DatabaseConnectionError,
    QueryExecutionError,
    QueryTimeoutError,
    UnsafeQueryError,
    AIServiceError,
    SessionNotFoundError
)
from utils.validation import (
    QueryType,
    classify_query_type,
    is_destructive_query,
    is_safe_query,
    sanitize_sql,
    validate_query_safety
)
from utils.security import (
    generate_cache_key,
    hash_connection_string,
    mask_password
)

__all__ = [
    "OptiVoxException",
    "DatabaseConnectionError",
    "QueryExecutionError",
    "QueryTimeoutError",
    "UnsafeQueryError",
    "AIServiceError",
    "SessionNotFoundError",
    "QueryType",
    "classify_query_type",
    "is_destructive_query",
    "is_safe_query",
    "sanitize_sql",
    "validate_query_safety",
    "generate_cache_key",
    "hash_connection_string",
    "mask_password"
]

