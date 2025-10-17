"""AI service integration with Gemini."""

from typing import Optional, Dict, Any
import json

from google import genai
from google.genai import types

from Core.Config import settings
from Core.Logging import logger
from utils.exceptions import AIServiceError
from utils.validation import sanitize_sql


class AIService:
    """Gemini AI service wrapper."""

    def __init__(self):
        """Initialize AI service."""
        self.client: Optional[genai.Client] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Gemini client."""
        if not settings.gemini_api_key:
            logger.warning("Gemini API key not configured")
            return

        try:
            self.client = genai.Client(api_key=settings.gemini_api_key)
            logger.info("Gemini AI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise AIServiceError(
                "Failed to initialize AI service",
                details={"error": str(e)}
            )

    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self.client is not None

    async def generate(
            self,
            prompt: str,
            system_instruction: Optional[str] = None,
            max_tokens: int = None,
            temperature: float = None
    ) -> str:
        """
        Generate content using Gemini AI.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            max_tokens: Maximum output tokens
            temperature: Sampling temperature

        Returns:
            Generated text

        Raises:
            AIServiceError: If generation fails
        """
        if not self.is_available():
            raise AIServiceError("AI service not available")

        if max_tokens is None:
            max_tokens = settings.ai_max_tokens
        if temperature is None:
            temperature = settings.ai_temperature

        try:
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            if system_instruction:
                config.system_instruction = system_instruction

            logger.debug(f"Generating AI response (temp={temperature})")

            response = self.client.models.generate_content(
                model=settings.default_model,
                contents=prompt,
                config=config
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise AIServiceError(
                f"Failed to generate AI response: {str(e)}",
                details={"prompt_length": len(prompt)}
            )

    async def generate_stream(
            self,
            prompt: str,
            system_instruction: Optional[str] = None,
            max_tokens: int = None,
            temperature: float = None
    ):
        """
        Stream content using Gemini AI.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            max_tokens: Maximum output tokens
            temperature: Sampling temperature

        Yields:
            Generated text chunks
        """
        if not self.is_available():
            yield "Error: AI service not available"
            return

        if max_tokens is None:
            max_tokens = settings.ai_max_tokens
        if temperature is None:
            temperature = settings.ai_temperature

        try:
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            if system_instruction:
                config.system_instruction = system_instruction

            logger.debug("Streaming AI response")

            for chunk in self.client.models.generate_content_stream(
                    model=settings.default_model,
                    contents=prompt,
                    config=config
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"AI streaming failed: {e}")
            yield f"Error: {str(e)}"

    async def natural_language_to_sql(
            self,
            prompt: str,
            schema_context: Dict[str, Any],
            conversation_history: Optional[list] = None
    ) -> str:
        """
        Convert natural language to SQL query.

        Args:
            prompt: User's natural language request
            schema_context: Database schema information
            conversation_history: Previous conversation context

        Returns:
            Generated SQL query
        """
        schema_description = json.dumps(schema_context, indent=2)

        system_instruction = """You are OptiVox DB, an expert SQL generator.
Your task is to convert natural language requests into valid, safe SQL queries.

Rules:
- Generate ONLY valid MySQL syntax
- Use exact table and column names from the schema
- Employ proper JOIN types and conditions
- Apply appropriate WHERE clauses and filters
- Use correct aggregate functions and GROUP BY
- Implement proper NULL handling
- Format queries for readability
- Add helpful comments for complex logic
- Use aliases for clarity
- Apply appropriate indexing hints when needed

QUERY CONSTRUCTION:
- Analyze natural language intent carefully
- Map user requirements to SQL operations
- Use schema context for table/column selection
- Consider relationships between tables
- Apply filters and conditions appropriately
- Optimize for performance from the start

SAFETY MEASURES:
- Never generate unprotected DELETE/UPDATE without WHERE
- Validate destructive operations require confirmation
- Warn about performance implications
- Suggest LIMIT clauses for large datasets

OUTPUT FORMAT:
Generate ONLY the SQL query without:
- Markdown code fences
- Explanatory text
- Unnecessary comments"""

        context_prompt = f"""Database Schema:
{schema_description}

User Request: {prompt}

Generate the SQL query:"""

        if conversation_history:
            recent_history = json.dumps(conversation_history[-3:], indent=2)
            context_prompt = f"""Previous context:
{recent_history}

{context_prompt}"""

        sql = await self.generate(
            context_prompt,
            system_instruction=system_instruction,
            temperature=0.3
        )

        return sanitize_sql(sql)

    def close(self) -> None:
        """Close AI client connection."""
        if self.client and hasattr(self.client, 'close'):
            try:
                self.client.close()
                logger.info("AI client closed")
            except Exception as e:
                logger.warning(f"Error closing AI client: {e}")


# Global AI service instance
ai_service = AIService()
