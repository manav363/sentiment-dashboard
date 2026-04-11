from __future__ import annotations

import logging
import os

from upstash_redis.asyncio import Redis

logger = logging.getLogger(__name__)


def _get_client() -> Redis | None:
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        logger.warning("Upstash env vars not set — caching disabled")
        return None
    return Redis(url=url, token=token)


async def cache_get(key: str) -> str | None:
    try:
        client = _get_client()
        if not client:
            return None
        return await client.get(key)
    except Exception as exc:
        logger.debug("Cache GET failed for key=%s: %s", key, exc)
        return None


async def cache_set(key: str, value: str, ttl: int) -> None:
    try:
        client = _get_client()
        if not client:
            return
        await client.set(key, value, ex=ttl)
    except Exception as exc:
        logger.debug("Cache SET failed for key=%s: %s", key, exc)


async def redis_connected() -> bool:
    try:
        client = _get_client()
        if not client:
            return False
        result = await client.ping()
        return result is True or result == "PONG"
    except Exception as exc:
        logger.debug("Redis health check failed: %s", exc)
        return False