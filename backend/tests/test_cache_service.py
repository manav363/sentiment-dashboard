import pytest
from app.services import cache_service
from redis.exceptions import RedisError


class FailingRedis:
    async def get(self, key: str) -> str | None:
        raise RedisError(f"GET failed for {key}")

    async def setex(self, key: str, ttl: int, value: str) -> None:
        raise RedisError(f"SETEX failed for {key} ttl={ttl} value={value}")

    async def ping(self) -> bool:
        raise RedisError("PING failed")


@pytest.mark.asyncio
async def test_cache_failures_do_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_service, "get_redis", lambda: FailingRedis())

    assert await cache_service.cache_get("sentiment:test:key") is None
    assert await cache_service.cache_set("sentiment:test:key", "{}", 60) is None
    assert await cache_service.redis_connected() is False
