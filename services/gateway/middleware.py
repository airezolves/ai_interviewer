"""Gateway middleware — CORS, rate limiting, request logging."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.utils.logger import get_logger

logger = get_logger("gateway.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()

        response = await call_next(request)

        duration = time.time() - start
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )

        return response
