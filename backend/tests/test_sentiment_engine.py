import asyncio
import importlib
import sys
from types import ModuleType

import pytest


@pytest.mark.asyncio
async def test_analyze_text_uses_parallel_chunk_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline_loader_stub = ModuleType("app.ml.pipeline_loader")
    pipeline_loader_stub.get_pipeline = lambda: None
    monkeypatch.setitem(sys.modules, "app.ml.pipeline_loader", pipeline_loader_stub)
    sys.modules.pop("app.services.sentiment_engine", None)
    sentiment_engine = importlib.import_module("app.services.sentiment_engine")

    active_calls = 0
    max_concurrency = 0

    async def fake_run_inference(_: str) -> dict[str, float]:
        nonlocal active_calls, max_concurrency
        active_calls += 1
        max_concurrency = max(max_concurrency, active_calls)
        await asyncio.sleep(0.01)
        active_calls -= 1
        return {"positive": 0.7, "neutral": 0.2, "negative": 0.1}

    monkeypatch.setattr(sentiment_engine, "_run_inference", fake_run_inference)

    result, chunk_count = await sentiment_engine.analyze_text_with_metadata("word " * 1000)

    assert chunk_count > 1
    assert max_concurrency > 1
    assert result.label == "positive"
    assert [item.label for item in result.breakdown] == ["positive", "neutral", "negative"]


@pytest.mark.asyncio
async def test_inference_truncates_to_the_models_token_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 400-word chunk can be longer than 512 tokens, so the pipeline must be told to truncate."""
    pipeline_loader_stub = ModuleType("app.ml.pipeline_loader")
    pipeline_loader_stub.get_pipeline = lambda: None
    monkeypatch.setitem(sys.modules, "app.ml.pipeline_loader", pipeline_loader_stub)
    sys.modules.pop("app.services.sentiment_engine", None)
    sentiment_engine = importlib.import_module("app.services.sentiment_engine")

    calls: list[dict] = []

    def fake_pipeline(text: str, **kwargs):
        calls.append(kwargs)
        return [
            [
                {"label": "LABEL_0", "score": 0.1},
                {"label": "LABEL_1", "score": 0.2},
                {"label": "LABEL_2", "score": 0.7},
            ]
        ]

    monkeypatch.setattr(sentiment_engine, "get_pipeline", lambda: fake_pipeline)

    scores = await sentiment_engine._run_inference("some text")

    assert scores == {"negative": 0.1, "neutral": 0.2, "positive": 0.7}
    assert calls == [{"truncation": True, "max_length": 512}]
