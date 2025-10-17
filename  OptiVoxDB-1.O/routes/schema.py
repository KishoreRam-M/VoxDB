"""Database schema introspection endpoints."""

from fastapi import APIRouter, HTTPException
import json

from Core.Logging import logger
from models.requests import SchemaAnalysisRequest, ConnectionModel
from models.response import StandardResponse
from services.ai_service import ai_service
from db.engine import get_engine, get_connection_key
from db.schema import get_schema_info, clear_schema_cache

router = APIRouter(prefix="/api/schema", tags=["Schema"])


@router.post("/info")
async def get_schema(connection: ConnectionModel, force_refresh: bool = False):
    """
    Get comprehensive schema information.

    Args:
        connection: Database connection parameters
        force_refresh: Force cache refresh

    Returns:
        Complete schema information
    """
    try:
        engine = get_engine(connection.model_dump())
        conn_key = get_connection_key(connection.model_dump())
        schema_info = await get_schema_info(engine, conn_key, force_refresh)

        return StandardResponse(
            success=True,
            data=schema_info
        )

    except Exception as e:
        logger.error(f"Schema introspection error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve schema: {str(e)}"
        )


@router.post("/analyze")
async def analyze_schema(request: SchemaAnalysisRequest):
    """
    AI-powered schema analysis with recommendations.

    Args:
        request: Schema analysis request

    Returns:
        Schema analysis with recommendations
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available"
        )

    try:
        # Get schema info
        engine = get_engine(request.connection.model_dump())
        conn_key = get_connection_key(request.connection.model_dump())
        schema_info = await get_schema_info(engine, conn_key)

        # Build analysis prompt
        system_instruction = """You are OptiVox DB performing expert schema analysis.

Analyze database schemas for design patterns, normalization, relationships, indexes,
performance, security, and scalability with actionable recommendations."""

        prompt = f"""Analyze this database schema:

{json.dumps(schema_info, indent=2)}

Analysis requirements:
- Recommendations: {'Yes' if request.include_recommendations else 'No'}
- Relationship analysis: {'Yes' if request.analyze_relationships else 'No'}

Provide comprehensive schema analysis with insights and improvements."""

        analysis = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.6,
            max_tokens=2500
        )

        return StandardResponse(
            success=True,
            data={
                "schema": schema_info,
                "analysis": analysis
            }
        )

    except Exception as e:
        logger.error(f"Schema analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema analysis failed: {str(e)}"
        )


@router.post("/clear-cache")
async def clear_cache(connection: ConnectionModel):
    """
    Clear schema cache for a connection.

    Args:
        connection: Database connection parameters

    Returns:
        Cache clear confirmation
    """
    conn_key = get_connection_key(connection.model_dump())
    clear_schema_cache(conn_key)

    return StandardResponse(
        success=True,
        data={"message": "Schema cache cleared"}
    )
