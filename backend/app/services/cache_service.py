from __future__ import annotations

import logging

from redis import asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import settings

_redis_client: aioredis.Redis | None = None
logger = logging.getLogger(__name__)


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def cache_get(key: str) -> str | None:
    try:
        return await get_redis().get(key)
    except (RedisError, OSError) as exc:
        logger.warning("Redis cache GET failed for key=%s: %s", key, exc)
        return None


async def cache_set(key: str, value: str, ttl: int) -> None:
    try:
        await get_redis().setex(key, ttl, value)
    except (RedisError, OSError) as exc:
        logger.warning("Redis cache SET failed for key=%s: %s", key, exc)
        return None


async def redis_connected() -> bool:
    try:
        return bool(await get_redis().ping())
    except (RedisError, OSError) as exc:
        logger.warning("Redis health check failed: %s", exc)
        return False
