"""Rate limiting middleware using Redis."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import redis.asyncio as redis
import time

from backend.gateway.app.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple sliding-window rate limiter using Redis."""

    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self._redis: redis.Redis | None = None
        self._redis_url = settings.redis_url

    async def _get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/health/ready"):
            return await call_next(request)

        # Extract user identifier (IP for unauthenticated, user_id for authenticated)
        client_ip = request.client.host if request.client else "unknown"
        identifier = client_ip  # Will be enhanced when auth is verified

        settings = get_settings()
        max_requests = settings.rate_limit_free_requests_per_minute

        try:
            r = await self._get_redis()
            key = f"ratelimit:{identifier}:{int(time.time()) // 60}"
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, 60)
            if current > max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"error": "RATE_LIMITED", "message": "Too many requests. Please slow down."},
                )
        except Exception:
            # If Redis is down, allow the request (fail-open)
            pass

        return await call_next(request)
