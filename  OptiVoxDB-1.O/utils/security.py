"""Security utilities and helpers."""

import hashlib
from typing import Optional


def generate_cache_key(*args: str) -> str:
    """
    Generate cache key from arguments.

    Args:
        *args: Strings to combine into cache key

    Returns:
        Cache key string
    """
    return "@".join(str(arg) for arg in args)


def hash_connection_string(
        user: str,
        host: str,
        port: int,
        database: str
) -> str:
    """
    Generate secure hash for connection string.

    Args:
        user: Database user
        host: Database host
        port: Database port
        database: Database name

    Returns:
        SHA256 hash of connection string
    """
    conn_str = f"{user}@{host}:{port}/{database}"
    return hashlib.sha256(conn_str.encode()).hexdigest()


def mask_password(password: str) -> str:
    """
    Mask password for logging.

    Args:
        password: Original password

    Returns:
        Masked password string
    """
    if len(password) <= 4:
        return "****"
    return f"{password[:2]}{'*' * (len(password) - 4)}{password[-2:]}"
