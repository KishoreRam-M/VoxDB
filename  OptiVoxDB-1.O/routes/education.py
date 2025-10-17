"""Educational content and learning endpoints."""

from fastapi import APIRouter, HTTPException
import json

from Core.Logging import logger
from models.requests import ExplanationRequest
from models.response import StandardResponse
from models.domain import DifficultyLevel
from services.ai_service import ai_service
from db.engine import get_engine, get_connection_key
from db.schema import get_schema_info

router = APIRouter(prefix="/api", tags=["Education"])


@router.post("/learn/explain")
async def explain_concept(request: ExplanationRequest):
    """
    Get educational explanation of database concept.

    Args:
        request: Explanation request with topic and difficulty

    Returns:
        Comprehensive educational content
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available"
        )

    try:
        # Validate difficulty level
        try:
            difficulty = DifficultyLevel(request.difficulty)
        except ValueError:
            difficulty = DifficultyLevel.BEGINNER

        # Build educational prompt
        system_instruction = """You are OptiVox DB, an expert database educator.

Create comprehensive, engaging educational content that explains concepts clearly,
uses practical examples, provides hands-on exercises, and connects to real-world applications."""

        # Get schema context if available
        schema_context = ""
        if request.connection:
            engine = get_engine(request.connection.model_dump())
            conn_key = get_connection_key(request.connection.model_dump())
            schema_info = await get_schema_info(engine, conn_key)
            schema_context = f"\n\nDatabase context available:\nTables: {list(schema_info['tables'].keys())}"

        prompt = f"""Topic: {request.topic}
Difficulty Level: {difficulty.value}
Include Examples: {'Yes' if request.include_examples else 'No'}
Include Exercises: {'Yes' if request.include_exercises else 'No'}{schema_context}

Provide a comprehensive educational explanation with:
1. Clear concept definition
2. Why it matters (practical importance)
3. How it works (mechanism/process)
4. Real-world examples
5. Best practices
6. Common mistakes to avoid
7. Practice exercises (if requested)
8. Further learning suggestions"""

        explanation = await ai_service.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.7,
            max_tokens=3000
        )

        return StandardResponse(
            success=True,
            data={
                "topic": request.topic,
                "difficulty": difficulty.value,
                "explanation": explanation
            }
        )

    except Exception as e:
        logger.error(f"Explanation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.get("/learn/topics")
async def get_learning_topics():
    """
    Get structured list of learning topics.

    Returns:
        Categorized learning topics
    """
    topics = {
        "fundamentals": [
            "SQL Basics",
            "SELECT Queries",
            "Filtering with WHERE",
            "Sorting with ORDER BY",
            "Data Types",
            "NULL Values",
            "Basic Functions"
        ],
        "intermediate": [
            "JOINs (INNER, LEFT, RIGHT, FULL)",
            "Aggregate Functions",
            "GROUP BY and HAVING",
            "Subqueries",
            "UNION and Set Operations",
            "Views",
            "Indexes"
        ],
        "advanced": [
            "Query Optimization",
            "Execution Plans",
            "Window Functions",
            "Common Table Expressions (CTEs)",
            "Transactions and ACID",
            "Concurrency Control",
            "Database Design and Normalization",
            "Partitioning",
            "Stored Procedures",
            "Triggers"
        ],
        "expert": [
            "Advanced Indexing Strategies",
            "Query Performance Tuning",
            "Deadlock Resolution",
            "Replication",
            "Sharding",
            "Database Security",
            "Backup and Recovery",
            "High Availability"
        ]
    }

    return StandardResponse(
        success=True,
        data=topics
    )
