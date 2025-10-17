"""Database engine management with connection pooling."""

from typing import Dict, Any
from sqlalchemy import create_engine, text, URL, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool

from Core.Config import settings
from Core.Logging import logger
from utils.security import generate_cache_key
from utils.exceptions import DatabaseConnectionError

# Global engine cache
_engine_cache: Dict[str, Engine] = {}


def get_connection_key(conn: Dict[str, Any]) -> str:
    """
    Generate unique cache key for database connection.

    Args:
        conn: Connection parameters dictionary

    Returns:
        Unique cache key string
    """
    return generate_cache_key(
        conn["user"],
        conn["host"],
        str(conn["port"]),
        conn["database"]
    )


def create_database_engine(
        conn: Dict[str, Any],
        pooled: bool = True
) -> Engine:
    """
    Create SQLAlchemy engine with proper configuration.

    Args:
        conn: Connection parameters
        pooled: Whether to use connection pooling

    Returns:
        Configured SQLAlchemy engine

    Raises:
        DatabaseConnectionError: If connection fails
    """
    url = URL.create(
        "mysql+pymysql",
        username=conn["user"],
        password=conn["password"],
        host=conn["host"],
        port=conn["port"],
        database=conn["database"],
    )

    engine_config = {
        "poolclass": QueuePool if pooled else NullPool,
        "pool_pre_ping": True,
        "echo": settings.enable_query_logging,
    }

    if pooled:
        engine_config.update({
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
        })

    try:
        engine = create_engine(url, **engine_config)

        # Test connection
        with engine.connect() as test_conn:
            test_conn.execute(text("SELECT 1"))

        logger.info(f"Database engine created: {conn['database']}@{conn['host']}")
        return engine

    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseConnectionError(
            f"Failed to connect to database: {str(e)}",
            details={"host": conn["host"], "database": conn["database"]}
        )


def get_engine(conn: Dict[str, Any], pooled: bool = True) -> Engine:
    """
    Get or create cached database engine.

    Args:
        conn: Connection parameters
        pooled: Whether to use connection pooling

    Returns:
        SQLAlchemy engine instance
    """
    key = get_connection_key(conn)

    # Check cache and validate existing connection
    if key in _engine_cache:
        try:
            with _engine_cache[key].connect() as test_conn:
                test_conn.execute(text("SELECT 1"))
            return _engine_cache[key]
        except Exception:
            logger.warning(f"Cached engine invalid, recreating: {key}")
            _engine_cache[key].dispose()
            del _engine_cache[key]

    # Create new engine
    engine = create_database_engine(conn, pooled)

    if pooled:
        _engine_cache[key] = engine

    return engine


def close_all_engines() -> None:
    """Close all cached database engines."""
    for key, engine in _engine_cache.items():
        try:
            engine.dispose()
            logger.info(f"Engine disposed: {key}")
        except Exception as e:
            logger.error(f"Error disposing engine {key}: {e}")

    _engine_cache.clear()
