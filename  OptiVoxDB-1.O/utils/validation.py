"""Query classification and validation utilities."""

import re
from enum import Enum
from typing import Tuple
from utils.exceptions import UnsafeQueryError


class QueryType(str, Enum):
    """SQL query types."""
    READ = "READ"
    WRITE = "WRITE"
    DDL = "DDL"
    DCL = "DCL"


# SQL Keywords Classification
READ_KEYWORDS = {"select", "show", "describe", "explain", "desc"}
DML_KEYWORDS = {"insert", "update", "delete", "replace"}
DDL_KEYWORDS = {"create", "alter", "drop", "truncate", "rename"}
DCL_KEYWORDS = {"grant", "revoke"}
DESTRUCTIVE_KEYWORDS = {"drop", "truncate", "delete"}


def classify_query_type(sql: str) -> QueryType:
    """
    Classify SQL query type based on first keyword.

    Args:
        sql: SQL query string

    Returns:
        QueryType enum value
    """
    first_word = sql.strip().lower().split()[0]

    if first_word in DDL_KEYWORDS:
        return QueryType.DDL
    elif first_word in DML_KEYWORDS:
        return QueryType.WRITE
    elif first_word in READ_KEYWORDS:
        return QueryType.READ
    elif first_word in DCL_KEYWORDS:
        return QueryType.DCL

    return QueryType.READ


def is_destructive_query(sql: str) -> bool:
    """
    Check if query is destructive (DROP, TRUNCATE, DELETE).

    Args:
        sql: SQL query string

    Returns:
        True if destructive, False otherwise
    """
    first_word = sql.strip().lower().split()[0]
    return first_word in DESTRUCTIVE_KEYWORDS


def is_safe_query(sql: str) -> Tuple[bool, str]:
    """
    Validate query for SQL injection patterns.

    Args:
        sql: SQL query string

    Returns:
        Tuple of (is_safe, reason)
    """
    sql_lower = sql.lower().strip()

    # Check for multiple statements
    if sql_lower.count(';') > 1:
        return False, "Multiple statements detected - potential SQL injection"

    # Check for SQL comments
    if '--' in sql or '/*' in sql or '*/' in sql:
        return False, "SQL comments detected - potential injection attempt"

    # Check for UNION-based injection
    if re.search(r'\bunion\b.*\bselect\b', sql_lower):
        return False, "UNION SELECT detected - potential injection"

    # Check for timing attacks
    if re.search(r'\b(sleep|benchmark|waitfor)\b', sql_lower):
        return False, "Timing attack functions detected"

    # Warn about information schema access
    if 'information_schema' in sql_lower:
        return True, "Information schema access detected (allowed with warning)"

    return True, "Query appears safe"

import re

def sanitize_sql(sql: str) -> str:
    """
    Sanitize SQL query by removing comments, markdown fences, and extra statements.

    Args:
        sql (str): Raw SQL query.

    Returns:
        str: Sanitized SQL query.
    """
    # Remove markdown code fences like ```sql or ```
    sql = re.sub(r'```[a-zA-Z]*', '', sql)
    sql = re.sub(r'```\n?', '', sql)

    # Remove inline and full-line SQL comments (-- comment)
    lines = []
    for line in sql.splitlines():
        line = re.sub(r'--.*$', '', line)  # remove comments
        if line.strip():                   # keep only non-empty lines
            lines.append(line)

    sql = '\n'.join(lines).strip()

    # Keep only the first SQL statement if multiple exist
    if sql.count(';') > 1:
        sql = sql.split(';')[0].strip() + ';'

    return sql



def validate_query_safety(sql: str, allow_destructive: bool = False) -> None:
    """
    Validate query safety and raise exception if unsafe.

    Args:
        sql: SQL query string
        allow_destructive: Whether to allow destructive operations

    Raises:
        UnsafeQueryError: If query is unsafe
    """
    is_safe, reason = is_safe_query(sql)
    if not is_safe:
        raise UnsafeQueryError(
            f"Query blocked for safety: {reason}",
            reason=reason,
            sql=sql
        )

    if is_destructive_query(sql) and not allow_destructive:
        raise UnsafeQueryError(
            "Destructive operation blocked",
            reason="Destructive query not allowed",
            sql=sql
        )
