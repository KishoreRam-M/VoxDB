"""Query processing and execution service."""

from typing import Dict, Any, Optional

from Core.Logging import logger
from models.domain import SessionContext
from services.ai_service import ai_service
from services.session_service import session_service
from db.query_executor import execute_query_safe
from utils.validation import validate_query_safety, is_destructive_query


class QueryService:
    """Handle natural language to SQL conversion and execution."""

    async def process_natural_query(
            self,
            prompt: str,
            schema_context: Dict[str, Any],
            engine,
            session: SessionContext,
            allow_destructive: bool,
            confirm: bool
    ) -> Dict[str, Any]:
        """
        Convert natural language to SQL and execute.

        Args:
            prompt: Natural language query
            schema_context: Database schema
            engine: SQLAlchemy engine
            session: Session context
            allow_destructive: Allow destructive operations
            confirm: Confirmation for destructive operations

        Returns:
            Query execution result
        """
        # Generate SQL from natural language
        sql = await ai_service.natural_language_to_sql(
            prompt,
            schema_context,
            session.conversation_history[-5:] if session.conversation_history else None
        )

        logger.info(f"Generated SQL: {sql}")

        # Safety validation
        try:
            validate_query_safety(sql, allow_destructive)
        except Exception as e:
            logger.warning(f"Query blocked: {str(e)}")
            return {
                "blocked": True,
                "message": str(e),
                "sql": sql,
                "success": False
            }

        # Destructive operation checks
        if is_destructive_query(sql):
            if not allow_destructive:
                return {
                    "blocked": True,
                    "message": "Destructive operation blocked. Set allow_destructive=true to proceed.",
                    "sql": sql,
                    "success": False
                }

            if not confirm:
                return {
                    "blocked": True,
                    "message": "Confirmation required for destructive operation. Set confirm=true.",
                    "sql": sql,
                    "success": False
                }

        # Execute query
        result = await execute_query_safe(engine, sql)

        # Update session context
        session_service.update_context(session, sql, result)

        return {**result, "sql": sql}
