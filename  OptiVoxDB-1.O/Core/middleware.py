"""Custom middleware for request processing."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from Core.Logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with correlation IDs."""

    async def dispatch(
            self,
            request: Request,
            call_next: Callable
    ) -> Response:
        """
        Process request with logging.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response object
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Log request
        start_time = time.time()
        logger.info(
            f"[{correlation_id}] {request.method} {request.url.path}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            f"[{correlation_id}] {response.status_code} "
            f"({duration:.3f}s)"
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response
