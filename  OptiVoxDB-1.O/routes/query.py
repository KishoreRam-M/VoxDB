"""Direct query execution endpoints."""

from fastapi import APIRouter, HTTPException
import json

from Core.Logging import logger
from models.requests import NaturalQueryRequest, OptimizationRequest, DebugRequest
from models.response import StandardResponse, QueryExecutionResponse
from models.domain import OperationMode
from services.query_service import QueryService
from services.session_service import session_service
from services.ai_service import ai_service
from db.engine import get_engine, get_connection_key
from db.schema import get_schema_info
from db.query_executor import execute_query_safe
from utils.validation import validate_query_safety, sanitize_sql

router = APIRouter(prefix="/api", tags=["Query"])
query_service = QueryService()


@router.post("/query/natural")
async def natural_language_query(request: NaturalQueryRequest):
    """
    Convert natural language to SQL and execute.

    Args:
        request: Natural query request

    Returns:
        Query execution result
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available"
        )

    try:
        # Get session and database context
        session = session_service.get_or_create(request.session_id)
        engine = get_engine(request.connection.model_dump())
        conn_key = get_connection_key(request.connection.model_dump())
        schema_info = await get_schema_info(engine, conn_key)

        # Process query
        result = await query_service.process_natural_query(
            prompt=request.prompt,
            schema_context=schema_info,
            engine=engine,
            session=session,
            allow_destructive=request.allow_destructive,
            confirm=request.confirm
        )

        return QueryExecutionResponse(**result)

    except Exception as e:
        logger.error(f"Natural query error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@router.post("/query/execute")
async def execute_sql(
        sql: str,
        connection: dict,
        allow_destructive: bool = False
):
    """
    Execute raw SQL query directly.

    Args:
        sql: SQL query string
        connection: Database connection parameters
        allow_destructive: Allow destructive operations

    Returns:
        Query execution result
    """
    try:
        # Sanitize and validate
        sql = sanitize_sql(sql)
        validate_query_safety(sql, allow_destructive)

        # Execute query
        engine = get_engine(connection)
        result = await execute_query_safe(engine, sql)

        return QueryExecutionResponse(**result)

    except Exception as e:
        logger.error(f"Query execution error: {e}", exc_info=True)
        return QueryExecutionResponse(
            success=False,
            query_type="UNKNOWN",
            error=str(e),
            error_type=type(e).__name__
        )


@router.post("/query/optimize")
async def optimize_query(request: OptimizationRequest):
    """
    Analyze and optimize SQL query.

    Args:
        request: Optimization request with SQL query

    Returns:
        Optimization analysis and recommendations
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available"
        )

    try:
        # Get schema context
        engine = get_engine(request.connection.model_dump())
        conn_key = get_connection_key(request.connection.model_dump())
        schema_info = await get_schema_info(engine, conn_key)

        # Build optimization prompt
        system_instruction = """You are OptiVox DB in Query Optimization Mode.

Analyze queries for performance and provide actionable optimization recommendations
including index strategies, query rewrites, and scalability improvements."""

        prompt = f"""Analyze and optimize this query:
        
Database Schema:
{json.dumps(schema_info, indent=2)}

Analysis Requirements:
- Execution plan analysis: {'Yes' if request.analyze_indexes else 'No'}
- Query rewrite suggestions: {'Yes' if request.suggest_rewrites else 'No'}

Provide comprehensive optimization recommendations."""

        optimization = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.5,
            max_tokens=2500
        )

        return StandardResponse(
            success=True,
            data={
                "original_query": request.sql,
                "optimization": optimization,
                "schema_analyzed": True
            }
        )

    except Exception as e:
        logger.error(f"Optimization error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )


@router.post("/query/debug")
async def debug_query(request: DebugRequest):
    """
    Debug problematic SQL query.

    Args:
        request: Debug request with SQL and error details

    Returns:
        Debugging analysis and solution
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available"
        )

    try:
        system_instruction = """You are OptiVox DB in Debug Mode.

Systematically diagnose database issues and provide clear, actionable solutions
with explanations and prevention strategies."""

        prompt = f"""Debug this SQL query:
        """

        if request.error_message:
            prompt += f"\nError message:\n{request.error_message}\n"

        prompt += """
Provide comprehensive debugging assistance:
1. Error diagnosis
2. Root cause analysis
3. Step-by-step solution
4. Corrected query
5. Prevention recommendations"""

        debug_response = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.6,
            max_tokens=2000
        )

        return StandardResponse(
            success=True,
            data={
                "original_query": request.sql,
                "error": request.error_message,
                "debug_analysis": debug_response
            }
        )

    except Exception as e:
        logger.error(f"Debug error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Debug failed: {str(e)}"
        )




