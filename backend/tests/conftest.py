"""Shared test fixtures for the sentiment-dashboard backend test suite."""

from __future__ import annotations

import sys
from types import ModuleType

import pytest


@pytest.fixture()
def stub_pipeline_loader(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Replace ``app.ml.pipeline_loader`` with a lightweight stub.

    The stub satisfies:
      * ``load_pipeline()``  → no-op (returns None)
      * ``get_pipeline()``   → returns None
      * ``is_pipeline_loaded()`` → returns True

    Modules that import from ``pipeline_loader`` are reloaded so they
    pick up the stub.  The caller can override individual attributes on
    the returned stub if finer control is needed.
    """
    stub = ModuleType("app.ml.pipeline_loader")
    stub.load_pipeline = lambda: None  # type: ignore[attr-defined]
    stub.get_pipeline = lambda: None  # type: ignore[attr-defined]
    stub.is_pipeline_loaded = lambda: True  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.ml.pipeline_loader", stub)

    # Force a reimport of downstream modules so they bind to the stub.
    dependent_modules = [
        "app.services.sentiment_engine",
        "app.api.sentiment",
        "app.api.url_scraper",
        "app.api",
        "main",
    ]
    for name in dependent_modules:
        sys.modules.pop(name, None)

    return stub


@pytest.fixture()
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch cache_service so every Redis call returns a safe default.

    * ``cache_get`` → always returns ``None`` (cache miss)
    * ``cache_set`` → no-op
    * ``redis_connected`` → returns ``False``
    """
    from app.services import cache_service

    async def _noop_get(_key: str) -> None:
        return None

    async def _noop_set(_key: str, _value: str, _ttl: int) -> None:
        return None

    async def _not_connected() -> bool:
        return False

    monkeypatch.setattr(cache_service, "cache_get", _noop_get)
    monkeypatch.setattr(cache_service, "cache_set", _noop_set)
    monkeypatch.setattr(cache_service, "redis_connected", _not_connected)
