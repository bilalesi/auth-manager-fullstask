"""Logging middleware for request/response tracking."""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and outgoing responses with structured logging."""

    async def dispatch(self, request: Request, call_next):
        """Log request details and response status with timing information."""
        start_time = time.time()

        logger.info(
            "incoming_request",
            method=request.method,
            path=str(request.url.path),
            client_host=request.client.host if request.client else None,
            query_params=str(request.url.query) if request.url.query else None,
        )

        response: Response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "request_completed",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
