"""The cache is optional by design: every failure mode must degrade to 'no cache'."""

import pytest

from app.services import cache_service


class FailingRedis:
    """Stands in for the Upstash client and fails every call."""

    async def get(self, key: str) -> str | None:
        raise ConnectionError(f"GET failed for {key}")

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError(f"SET failed for {key} ex={ex}")

    async def ping(self) -> bool:
        raise ConnectionError("PING failed")


class WorkingRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    async def ping(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_cache_failures_do_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_service, "_get_client", lambda: FailingRedis())

    assert await cache_service.cache_get("sentiment:test:key") is None
    assert await cache_service.cache_set("sentiment:test:key", "{}", 60) is None
    assert await cache_service.redis_connected() is False


@pytest.mark.asyncio
async def test_cache_is_disabled_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    assert await cache_service.cache_get("k") is None
    assert await cache_service.cache_set("k", "v", 60) is None
    assert await cache_service.redis_connected() is False


@pytest.mark.asyncio
async def test_cache_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = WorkingRedis()
    monkeypatch.setattr(cache_service, "_get_client", lambda: fake)

    await cache_service.cache_set("k", "value", 60)

    assert await cache_service.cache_get("k") == "value"
    assert await cache_service.redis_connected() is True
