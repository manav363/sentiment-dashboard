import importlib
import sys
from types import ModuleType

from fastapi.testclient import TestClient


def test_health_reports_model_and_redis_status(monkeypatch) -> None:
    pipeline_loader_stub = ModuleType("app.ml.pipeline_loader")
    pipeline_loader_stub.load_pipeline = lambda: None
    pipeline_loader_stub.is_pipeline_loaded = lambda: True
    pipeline_loader_stub.get_pipeline = lambda: None
    monkeypatch.setitem(sys.modules, "app.ml.pipeline_loader", pipeline_loader_stub)
    module_names = [
        "main",
        "app.api",
        "app.api.sentiment",
        "app.api.url_scraper",
        "app.services.sentiment_engine",
    ]
    for module_name in module_names:
        sys.modules.pop(module_name, None)
    main = importlib.import_module("main")

    monkeypatch.setattr(main, "load_pipeline", lambda: None)
    monkeypatch.setattr(main, "is_pipeline_loaded", lambda: True)

    async def fake_redis_connected() -> bool:
        return False

    monkeypatch.setattr(main, "redis_connected", fake_redis_connected)

    with TestClient(main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_loaded": True,
        "redis_connected": False,
    }
    assert response.headers["X-Request-ID"]
