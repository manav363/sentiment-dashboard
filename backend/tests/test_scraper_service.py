import socket

import pytest
from app.services import scraper_service
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_validate_public_url_rejects_private_targets() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.validate_public_url("http://127.0.0.1:8000/internal")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_public_url_rejects_resolved_private_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        scraper_service.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.12", 443)),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.validate_public_url("https://example.com/article")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_scrape_url_falls_back_to_httpx_when_trafilatura_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Make trafilatura.fetch_url return None so the primary path fails
    monkeypatch.setattr(
        scraper_service.trafilatura,
        "fetch_url",
        lambda _url: None,
    )
    monkeypatch.setattr(
        scraper_service.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        ],
    )

    class FakeResponse:
        text = (
            "<html><head><title>Fallback title</title></head>"
            "<body>"
            "<p>This is a sufficiently long paragraph to pass the"
            " minimum length filter in the scraper.</p>"
            "</body></html>"
        )

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str, **kwargs) -> FakeResponse:
            assert url == "https://example.com/article"
            return FakeResponse()

    monkeypatch.setattr(scraper_service.httpx, "AsyncClient", lambda **kwargs: FakeClient())

    title, body_text = await scraper_service.scrape_url("https://example.com/article")

    assert title == "Fallback title"
    assert "sufficiently long paragraph" in body_text


@pytest.mark.asyncio
async def test_scrape_url_raises_when_trafilatura_exception_and_no_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Make trafilatura raise an exception so the primary path fails
    def failing_fetch(_url):
        raise RuntimeError("trafilatura download failed")

    monkeypatch.setattr(scraper_service.trafilatura, "fetch_url", failing_fetch)
    monkeypatch.setattr(
        scraper_service.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
        ],
    )

    class FakeResponse:
        text = "<html><head><title>Empty</title></head><body><p>Short</p></body></html>"

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str, **kwargs) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(scraper_service.httpx, "AsyncClient", lambda **kwargs: FakeClient())

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.scrape_url("https://example.com/article")

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_validate_public_url_rejects_localhost() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.validate_public_url("http://localhost/secret")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_public_url_rejects_non_http_scheme() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.validate_public_url("ftp://example.com/file")

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_public_url_rejects_unresolvable_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DNS resolution failure must block the request to prevent DNS rebinding."""

    def failing_getaddrinfo(*args, **kwargs):
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr(scraper_service.socket, "getaddrinfo", failing_getaddrinfo)

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.validate_public_url("https://evil-rebind.example.com/steal")

    assert exc_info.value.status_code == 400
    assert "resolve" in exc_info.value.detail.lower()

