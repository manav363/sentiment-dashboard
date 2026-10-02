import socket

import httpx
import pytest
from fastapi import HTTPException

from app.services import scraper_service


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


PUBLIC_IP = "93.184.216.34"

ARTICLE_HTML = (
    "<html><head><title>Markets rally</title></head><body>"
    "<nav>Home | About</nav>"
    "<article><h1>Markets rally on rate cut hopes</h1>"
    "<p>Stocks climbed on Friday as investors bet that the central bank would cut rates at"
    " its next meeting, lifting technology shares in particular.</p>"
    "<p>Analysts said the move reflected improving sentiment, although several cautioned that"
    " inflation data remains the key risk to the rally over the coming weeks.</p>"
    "<p>Trading volumes were above their recent average, and bond yields eased across the"
    " curve as the session progressed into the afternoon.</p>"
    "</article><footer>Copyright 2026</footer></body></html>"
)


@pytest.fixture
def serve(monkeypatch: pytest.MonkeyPatch):
    """Route all scraper traffic to a handler instead of the network.

    Every hostname resolves to a public IP unless it is already an IP literal, so these tests
    exercise the redirect logic rather than DNS.
    """
    requested: list[str] = []
    real_client = httpx.AsyncClient

    def install(handler) -> list[str]:
        def recording(request: httpx.Request) -> httpx.Response:
            requested.append(str(request.url))
            return handler(request)

        monkeypatch.setattr(
            scraper_service.httpx,
            "AsyncClient",
            lambda **kwargs: real_client(transport=httpx.MockTransport(recording), **kwargs),
        )
        monkeypatch.setattr(
            scraper_service.socket,
            "getaddrinfo",
            lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (PUBLIC_IP, 443))],
        )
        return requested

    return install


@pytest.mark.asyncio
async def test_scrape_url_extracts_article_with_trafilatura(serve) -> None:
    serve(lambda request: httpx.Response(200, text=ARTICLE_HTML))

    title, body = await scraper_service.scrape_url("https://news.example.com/story")

    assert "rate cut" in body
    assert "Trading volumes" in body
    assert "Copyright" not in body
    assert title


@pytest.mark.asyncio
async def test_scrape_url_falls_back_to_beautifulsoup_when_trafilatura_finds_nothing(
    serve, monkeypatch: pytest.MonkeyPatch
) -> None:
    html = (
        "<html><head><title>Fallback title</title></head><body>"
        "<p>This is a sufficiently long paragraph to pass the minimum length filter.</p>"
        "</body></html>"
    )
    serve(lambda request: httpx.Response(200, text=html))
    monkeypatch.setattr(scraper_service.trafilatura, "extract", lambda *a, **k: None)

    title, body = await scraper_service.scrape_url("https://example.com/article")

    assert title == "Fallback title"
    assert "sufficiently long paragraph" in body


@pytest.mark.asyncio
async def test_scrape_url_falls_back_when_trafilatura_raises(
    serve, monkeypatch: pytest.MonkeyPatch
) -> None:
    html = (
        "<html><head><title>Still works</title></head><body>"
        "<p>This is a sufficiently long paragraph to pass the minimum length filter.</p>"
        "</body></html>"
    )
    serve(lambda request: httpx.Response(200, text=html))

    def boom(*args, **kwargs):
        raise RuntimeError("extraction failed")

    monkeypatch.setattr(scraper_service.trafilatura, "extract", boom)

    title, body = await scraper_service.scrape_url("https://example.com/article")

    assert title == "Still works"
    assert "sufficiently long paragraph" in body


@pytest.mark.asyncio
async def test_scrape_url_raises_422_when_page_has_no_usable_text(
    serve, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve(
        lambda request: httpx.Response(
            200, text="<html><head><title>Empty</title></head><body><p>Short</p></body></html>"
        )
    )
    monkeypatch.setattr(scraper_service.trafilatura, "extract", lambda *a, **k: None)

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.scrape_url("https://example.com/article")

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_redirect_to_internal_address_is_blocked(serve) -> None:
    """A public page must not be able to bounce us to the cloud metadata endpoint."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "news.example.com":
            return httpx.Response(
                302, headers={"location": "http://169.254.169.254/latest/meta-data/"}
            )
        return httpx.Response(200, text="SECRET")

    requested = serve(handler)

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.scrape_url("https://news.example.com/story")

    assert exc_info.value.status_code == 400
    assert requested == ["https://news.example.com/story"]  # the internal URL was never fetched


@pytest.mark.asyncio
async def test_redirect_to_localhost_is_blocked(serve) -> None:
    requested = serve(
        lambda request: httpx.Response(302, headers={"location": "http://localhost:8000/health"})
    )

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.scrape_url("https://news.example.com/story")

    assert exc_info.value.status_code == 400
    assert len(requested) == 1


@pytest.mark.asyncio
async def test_public_redirects_are_followed_including_relative_ones(serve) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/old":
            return httpx.Response(301, headers={"location": "/new"})
        if request.url.path == "/new":
            return httpx.Response(302, headers={"location": "https://cdn.example.org/final"})
        return httpx.Response(200, text=ARTICLE_HTML)

    requested = serve(handler)

    _, body = await scraper_service.scrape_url("https://news.example.com/old")

    assert "rate cut" in body
    assert requested == [
        "https://news.example.com/old",
        "https://news.example.com/new",
        "https://cdn.example.org/final",
    ]


@pytest.mark.asyncio
async def test_redirect_loop_is_cut_off(serve) -> None:
    requested = serve(lambda request: httpx.Response(302, headers={"location": "/again"}))

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.scrape_url("https://news.example.com/loop")

    assert exc_info.value.status_code == 422
    assert len(requested) == scraper_service.MAX_REDIRECTS + 1


@pytest.mark.asyncio
async def test_upstream_errors_become_502_not_500(serve) -> None:
    serve(lambda request: httpx.Response(503, text="down"))

    with pytest.raises(HTTPException) as exc_info:
        await scraper_service.scrape_url("https://news.example.com/story")

    assert exc_info.value.status_code == 502


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
