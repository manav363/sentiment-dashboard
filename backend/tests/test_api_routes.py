from __future__ import annotations

import importlib
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.models.response import ScoreBreakdown, SentimentResult

MOCK_SENTIMENT_RESULT = SentimentResult(
    label="positive",
    score=0.92,
    breakdown=[
        ScoreBreakdown(label="positive", score=0.92),
        ScoreBreakdown(label="neutral", score=0.06),
        ScoreBreakdown(label="negative", score=0.02),
    ],
    text_preview="I love this product so much",
)


@pytest.fixture()
def client(
    stub_pipeline_loader: object,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setattr("app.api.sentiment.cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr("app.api.sentiment.cache_set", AsyncMock(return_value=None))
    monkeypatch.setattr("app.api.url_scraper.cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr("app.api.url_scraper.cache_set", AsyncMock(return_value=None))

    main_module = importlib.import_module("main")
    main_module.get_pipeline = lambda: MagicMock()

    with TestClient(main_module.app) as test_client:
        yield test_client


class TestSentimentAnalyzeEndpoint:
    def test_returns_200_with_valid_text(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "app.api.sentiment.analyze_text",
            AsyncMock(return_value=MOCK_SENTIMENT_RESULT),
        )
        response = client.post(
            "/api/sentiment/analyze",
            json={"text": "I love this product so much"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "positive"
        assert data["score"] == pytest.approx(0.92)
        assert len(data["breakdown"]) == 3

    def test_returns_422_for_text_too_short(self, client: TestClient) -> None:
        response = client.post(
            "/api/sentiment/analyze",
            json={"text": "Hi"},
        )
        assert response.status_code == 422

    def test_returns_422_for_empty_text(self, client: TestClient) -> None:
        response = client.post(
            "/api/sentiment/analyze",
            json={"text": ""},
        )
        assert response.status_code == 422

    def test_returns_422_for_missing_text_field(self, client: TestClient) -> None:
        response = client.post("/api/sentiment/analyze", json={})
        assert response.status_code == 422

    def test_returns_413_for_oversized_body(self, client: TestClient) -> None:
        response = client.post(
            "/api/sentiment/analyze",
            content=b"x" * 70_000,
            headers={"Content-Type": "application/json", "Content-Length": "70000"},
        )
        assert response.status_code == 413

    def test_x_request_id_header_present(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "app.api.sentiment.analyze_text",
            AsyncMock(return_value=MOCK_SENTIMENT_RESULT),
        )
        response = client.post(
            "/api/sentiment/analyze",
            json={"text": "This is a test sentence for request ID."},
        )
        assert "x-request-id" in response.headers

    def test_accepts_client_provided_request_id(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "app.api.sentiment.analyze_text",
            AsyncMock(return_value=MOCK_SENTIMENT_RESULT),
        )
        response = client.post(
            "/api/sentiment/analyze",
            json={"text": "Testing request ID passthrough."},
            headers={"X-Request-ID": "my-custom-id-123"},
        )
        assert response.headers.get("x-request-id") == "my-custom-id-123"


class TestURLAnalyzeEndpoint:
    def test_returns_200_with_valid_url(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "app.api.url_scraper.scrape_url",
            AsyncMock(return_value=("Article Title", "This is the article body text.")),
        )
        monkeypatch.setattr(
            "app.api.url_scraper.analyze_text_with_metadata",
            AsyncMock(return_value=(MOCK_SENTIMENT_RESULT, 1)),
        )
        response = client.post(
            "/api/url/analyze",
            json={"url": "https://example.com/article"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Article Title"
        assert data["result"]["label"] == "positive"

    def test_returns_422_for_invalid_url(self, client: TestClient) -> None:
        response = client.post(
            "/api/url/analyze",
            json={"url": "not-a-url"},
        )
        assert response.status_code == 422

    def test_returns_422_for_missing_url_field(self, client: TestClient) -> None:
        response = client.post("/api/url/analyze", json={})
        assert response.status_code == 422
