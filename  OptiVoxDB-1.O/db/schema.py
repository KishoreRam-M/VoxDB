"""Database schema introspection utilities."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import Engine, inspect

from Core.Logging import logger

# Global schema cache
_schema_cache: Dict[str, Dict[str, Any]] = {}
SCHEMA_CACHE_TTL = 300  # 5 minutes


async def get_schema_info(
        engine: Engine,
        conn_key: str,
        force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Get comprehensive schema information with caching.

    Args:
        engine: SQLAlchemy engine
        conn_key: Connection cache key
        force_refresh: Force cache refresh

    Returns:
        Schema information dictionary
    """
    # Check cache
    if not force_refresh and conn_key in _schema_cache:
        cache_entry = _schema_cache[conn_key]
        cache_time = cache_entry.get("timestamp")

        if cache_time and (datetime.utcnow() - cache_time).seconds < SCHEMA_CACHE_TTL:
            logger.debug(f"Schema cache hit: {conn_key}")
            return cache_entry["data"]

    # Build schema info
    schema_info = {
        "tables": {},
        "relationships": [],
        "indexes": {}
    }

    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        logger.info(f"Introspecting {len(table_names)} tables...")

        for table_name in table_names:
            # Get columns
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "default": column.get("default"),
                    "primary_key": column.get("primary_key", False)
                })

            # Get constraints
            pk = inspector.get_pk_constraint(table_name)
            fks = inspector.get_foreign_keys(table_name)
            indexes = inspector.get_indexes(table_name)

            schema_info["tables"][table_name] = {
                "columns": columns,
                "primary_key": pk,
                "foreign_keys": fks,
                "indexes": indexes
            }

            # Build relationships
            for fk in fks:
                schema_info["relationships"].append({
                    "from_table": table_name,
                    "to_table": fk["referred_table"],
                    "columns": list(zip(
                        fk["constrained_columns"],
                        fk["referred_columns"]
                    ))
                })

        # Cache result
        _schema_cache[conn_key] = {
            "data": schema_info,
            "timestamp": datetime.utcnow()
        }

        logger.info(f"Schema introspection complete: {conn_key}")
        return schema_info

    except Exception as e:
        logger.error(f"Schema introspection failed: {e}")
        return schema_info


def clear_schema_cache(conn_key: Optional[str] = None) -> None:
    """
    Clear schema cache.

    Args:
        conn_key: Specific connection key, or None to clear all
    """
    if conn_key:
        if conn_key in _schema_cache:
            del _schema_cache[conn_key]
            logger.info(f"Schema cache cleared: {conn_key}")
    else:
        _schema_cache.clear()
        logger.info("All schema caches cleared")
