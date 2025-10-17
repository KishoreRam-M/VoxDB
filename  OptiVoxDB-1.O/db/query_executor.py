"""Safe query execution with timeout and error handling."""

from typing import Dict, Any, Optional
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from Core.Config import settings
from Core.Logging import logger
from utils.validation import classify_query_type, QueryType
from utils.exceptions import QueryExecutionError, QueryTimeoutError


async def execute_query_safe(
        engine: Engine,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = None
) -> Dict[str, Any]:
    """
    Execute SQL query with safety checks and timeout.

    Args:
        engine: SQLAlchemy engine
        sql: SQL query string
        params: Query parameters
        timeout: Execution timeout in seconds

    Returns:
        Query execution result dictionary

    Raises:
        QueryTimeoutError: If query exceeds timeout
        QueryExecutionError: If query execution fails
    """
    if timeout is None:
        timeout = settings.max_query_execution_time

    query_type = classify_query_type(sql)

    logger.info(f"Executing {query_type.value} query")
    logger.debug(f"SQL: {sql}")

    try:
        with engine.connect() as conn:
            # Set execution timeout
            conn.execute(text(f"SET SESSION MAX_EXECUTION_TIME={timeout * 1000}"))

            # Execute query
            if params:
                result = conn.execute(text(sql), params)
            else:
                result = conn.execute(text(sql))

            # Process results
            if result.returns_rows:
                rows = [dict(row._mapping) for row in result.fetchall()]

                logger.info(f"Query returned {len(rows)} rows")

                return {
                    "success": True,
                    "query_type": query_type.value,
                    "data": rows,
                    "row_count": len(rows),
                    "columns": list(rows[0].keys()) if rows else []
                }
            else:
                # Commit write operations
                if query_type in [QueryType.WRITE, QueryType.DDL]:
                    conn.commit()

                logger.info(f"Query affected {result.rowcount} rows")

                return {
                    "success": True,
                    "query_type": query_type.value,
                    "message": "Query executed successfully",
                    "rows_affected": result.rowcount
                }

    except OperationalError as e:
        error_msg = str(e).lower()

        if "timeout" in error_msg or "max_execution_time" in error_msg:
            logger.error(f"Query timeout after {timeout}s")
            raise QueryTimeoutError(
                f"Query execution exceeded {timeout} seconds",
                timeout=timeout
            )

        logger.error(f"Operational error: {e}")
        raise QueryExecutionError(
            f"Database operational error: {str(e)}",
            details={"error_type": "operational", "sql": sql}
        )

    except SQLAlchemyError as e:
        logger.error(f"SQL error: {e}")
        raise QueryExecutionError(
            f"SQL execution error: {str(e)}",
            details={"error_type": "sql_error", "sql": sql}
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise QueryExecutionError(
            f"Unexpected error during query execution: {str(e)}",
            details={"error_type": "unknown", "sql": sql}
        )


async def simulate_query(
        sql: str,
        schema_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulate query execution without actually running it.

    Args:
        sql: SQL query string
        schema_info: Database schema information

    Returns:
        Simulation result dictionary
    """
    query_type = classify_query_type(sql)

    logger.info(f"Simulating {query_type.value} query")

    return {
        "mode": "simulation",
        "query_type": query_type.value,
        "sql": sql,
        "validation": {
            "syntax": "valid",
            "tables_accessed": [],
            "estimated_complexity": "medium"
        },
        "simulation_note": "Query not executed - simulation mode active"
    }
