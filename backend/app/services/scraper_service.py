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


async def scrape_url(url: str) -> tuple[str, str]:
    await validate_public_url(url)

    # --- Primary: trafilatura ---
    try:
        downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
        if downloaded:
            body = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                no_fallback=False,
            )
            # Extract title via trafilatura metadata
            metadata = trafilatura.extract_metadata(downloaded)
            title = metadata.title if metadata and metadata.title else url
            if body:
                return clean_text(title), clean_text(body)
    except Exception as e:
        logger.debug("Trafilatura extraction failed, falling back to httpx: %s", e)

    # --- Fallback: httpx + BeautifulSoup4 ---
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "SentiScope/1.0"})
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url
    paragraphs = soup.find_all("p")
    body = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 40)

    if not body:
        raise HTTPException(status_code=422, detail="Could not extract article text from this URL.")

    return clean_text(title), clean_text(body)
