from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup
from fastapi import HTTPException

from app.core.request_context import get_request_id
from app.ml.text_preprocessor import clean_text

logger = logging.getLogger(__name__)
BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}
MAX_REDIRECTS = 5
USER_AGENT = "SentiScope/1.0"


def _is_blocked_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return any(
        (
            address.is_loopback,
            address.is_private,
            address.is_link_local,
            address.is_multicast,
            address.is_unspecified,
            address.is_reserved,
        )
    )


async def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only HTTP and HTTPS URLs are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL must include a valid hostname.")

    normalized_hostname = hostname.rstrip(".").lower()
    if normalized_hostname in BLOCKED_HOSTS or normalized_hostname.endswith(".localhost"):
        raise HTTPException(status_code=400, detail="Unsafe URL target is not allowed.")

    try:
        if _is_blocked_ip(normalized_hostname):
            raise HTTPException(status_code=400, detail="Unsafe URL target is not allowed.")
    except ValueError:
        pass

    try:
        host_records = await asyncio.to_thread(
            socket.getaddrinfo,
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        logger.warning(
            "Host resolution failed during SSRF validation request_id=%s url=%s error=%s",
            get_request_id(),
            url,
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail="Could not resolve hostname. Please verify the URL and try again.",
        ) from exc

    for record in host_records:
        ip_value = record[4][0]
        if _is_blocked_ip(ip_value):
            raise HTTPException(status_code=400, detail="Unsafe URL target is not allowed.")


async def fetch_public_html(url: str) -> str:
    """Fetch a page, validating the URL *and every redirect hop* against the SSRF rules.

    Following redirects blindly would let a public page answer ``302 Location:
    http://169.254.169.254/...`` and have us fetch an internal address for it, so
    redirects are followed by hand and each target goes through ``validate_public_url``.
    """
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            current = url
            for _ in range(MAX_REDIRECTS + 1):
                await validate_public_url(current)
                response = await client.get(current, headers={"User-Agent": USER_AGENT})
                if not response.is_redirect:
                    response.raise_for_status()
                    return response.text
                location = response.headers.get("location")
                if not location:
                    break
                current = str(response.url.join(location))
    except httpx.HTTPError as exc:
        logger.warning(
            "Fetching URL failed request_id=%s url=%s error=%s", get_request_id(), url, exc
        )
        raise HTTPException(status_code=502, detail="Could not fetch the URL.") from exc

    raise HTTPException(status_code=422, detail="Too many redirects.")


async def scrape_url(url: str) -> tuple[str, str]:
    html = await fetch_public_html(url)

    # --- Primary: trafilatura ---
    try:
        body = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
        )
        if body:
            metadata = trafilatura.extract_metadata(html)
            title = metadata.title if metadata and metadata.title else url
            return clean_text(title), clean_text(body)
    except Exception as e:
        logger.debug("Trafilatura extraction failed, falling back to BeautifulSoup: %s", e)

    # --- Fallback: BeautifulSoup4 over the same HTML ---
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url
    paragraphs = soup.find_all("p")
    body = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)

    if not body:
        raise HTTPException(status_code=422, detail="Could not extract article text from this URL.")

    return clean_text(title), clean_text(body)
