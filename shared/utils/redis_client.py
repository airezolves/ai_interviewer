"""Redis client for caching and message queues."""

import redis.asyncio as redis

from shared.config.base_settings import get_base_settings

settings = get_base_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """FastAPI dependency that provides a Redis client."""
    return redis_client


async def close_redis():
    """Close the Redis connection."""
    await redis_client.close()
