"""Request ID middleware for tracking requests."""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# TODO: add monitoring to the system
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and attach unique request IDs to each request."""

    async def dispatch(self, request: Request, call_next):
        """
        Generate a unique request ID for each incoming request.
        """

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id

            return response
        finally:
            structlog.contextvars.clear_contextvars()
