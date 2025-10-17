"""Chat conversation endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from Core.Logging import logger
from models.requests import ChatRequest
from models.response import StandardResponse, ChatResponse
from models.domain import OperationMode
from services.chat_service import chat_service
from services.ai_service import ai_service
from services.session_service import session_service
from db.engine import get_engine, get_connection_key
from db.schema import get_schema_info

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Primary chat interface with multi-mode support.

    This is the main endpoint for conversational interactions with OptiVox DB.
    Supports multiple operation modes for different use cases.

    Args:
        request: Chat request with message and configuration

    Returns:
        Chat response with AI-generated reply
    """
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service not available"
        )

    try:
        # Validate mode
        try:
            mode = OperationMode(request.mode)
        except ValueError:
            mode = OperationMode.ASSISTANT

        # Handle streaming response
        if request.stream:
            return StreamingResponse(
                _stream_chat_response(request, mode),
                media_type="text/event-stream"
            )

        # Process chat message
        result = await chat_service.process_chat_message(
            message=request.message,
            connection=request.connection.model_dump(),
            session_id=request.session_id,
            mode=mode,
            allow_destructive=request.allow_destructive,
            confirm=request.confirm
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


async def _stream_chat_response(request: ChatRequest, mode: OperationMode):
    """
    Stream chat response in real-time.

    Args:
        request: Chat request
        mode: Operation mode

    Yields:
        Server-sent events with response chunks
    """
    try:
        # Get or create session
        session = session_service.get_or_create(request.session_id)
        session_service.add_message(session.session_id, "user", request.message)

        # Get database connection and schema
        engine = get_engine(request.connection.model_dump())
        conn_key = get_connection_key(request.connection.model_dump())
        schema_info = await get_schema_info(engine, conn_key)

        # Get chat history
        chat_history = session_service.get_chat_history(session.session_id)

        # Build system instruction based on mode
        system_instruction = _get_system_instruction_for_mode(mode)

        # Build prompt with context
        prompt = _build_streaming_prompt(
            request.message,
            mode,
            schema_info,
            chat_history
        )

        # Send initial metadata
        yield f"data: {json.dumps({'type': 'start', 'session_id': session.session_id})}\n\n"

        # Stream AI response
        full_response = ""
        async for chunk in ai_service.generate_stream(
                prompt,
                system_instruction=system_instruction
        ):
            full_response += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        # Save response to session
        session_service.add_message(
            session.session_id,
            "assistant",
            full_response,
            {"mode": mode.value, "streamed": True}
        )

        # Send completion event
        yield f"data: {json.dumps({'type': 'done', 'full_response': full_response})}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


def _get_system_instruction_for_mode(mode: OperationMode) -> str:
    """Get optimized system instruction for operation mode."""

    instructions = {
        OperationMode.ASSISTANT: """You are OptiVox DB - The World's Most Advanced AI Database Assistant.

You combine deep technical expertise with natural conversational abilities, context awareness,
and proactive intelligence to provide the best database assistance possible.

Respond naturally, professionally, and helpfully to all database-related queries.""",

        OperationMode.TEACHING: """You are OptiVox DB in Teaching Mode - The World's Best Database Educator.

Transform complex database concepts into crystal-clear understanding through exceptional
pedagogy, real-world examples, and progressive learning methodology.""",

        OperationMode.DEBUG: """You are OptiVox DB in Debug Mode - Elite Database Troubleshooter.

Systematically diagnose and resolve database issues with expert analysis, clear solutions,
and preventive recommendations.""",

        OperationMode.OPTIMIZATION: """You are OptiVox DB in Optimization Mode - Elite Performance Specialist.

Analyze queries for performance bottlenecks and provide actionable optimization recommendations
with index strategies and query rewrites.""",

        OperationMode.QUERY: """You are OptiVox DB in Query Mode - Expert SQL Generator.

Convert natural language to optimized, production-ready SQL queries using proper syntax,
schema awareness, and best practices."""
    }

    return instructions.get(mode, instructions[OperationMode.ASSISTANT])


def _build_streaming_prompt(
        message: str,
        mode: OperationMode,
        schema_info: dict,
        chat_history: list
) -> str:
    """Build optimized prompt for streaming responses."""

    # Schema summary
    table_names = list(schema_info.get('tables', {}).keys())
    schema_summary = f"Database tables: {', '.join(table_names[:10])}"
    if len(table_names) > 10:
        schema_summary += f" (and {len(table_names) - 10} more)"

    # Recent conversation context
    history_text = ""
    if chat_history:
        recent = chat_history[-3:]
        history_text = "Recent conversation:\n"
        for msg in recent:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]
            history_text += f"{role}: {content}\n"

    # Build prompt
    prompt = f"""{schema_summary}

{history_text}
User: {message}

Respond as OptiVox DB:"""

    return prompt


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Chat history messages
    """
    try:
        session = session_service.get(session_id)
        history = session_service.get_chat_history(session_id)

        return StandardResponse(
            success=True,
            data={
                "session_id": session_id,
                "history": history,
                "message_count": len(history)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
