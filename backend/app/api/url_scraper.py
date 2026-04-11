from hashlib import sha256

from fastapi import APIRouter, HTTPException, Request

from app.core.rate_limiter import EXTERNAL_LIMIT, limiter
from app.ml.model_config import CACHE_TTL_SECONDS
from app.models.request import AnalyzeURLRequest
from app.models.response import URLAnalysisResult
from app.services.cache_service import cache_get, cache_set
from app.services.scraper_service import scrape_url
from app.services.sentiment_engine import analyze_text_with_metadata

router = APIRouter()


@router.post("/analyze", response_model=URLAnalysisResult)
@limiter.limit(EXTERNAL_LIMIT)
async def analyze_url(request: Request, payload: AnalyzeURLRequest) -> URLAnalysisResult:  # noqa: ARG001 — required by @limiter.limit
    url_str = str(payload.url)
    cache_key = f"sentiment:url:{sha256(url_str.encode('utf-8')).hexdigest()}"
    cached = await cache_get(cache_key)
    if cached:
        return URLAnalysisResult.model_validate_json(cached)

    title, body_text = await scrape_url(url_str)

    if not body_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract article text from the provided URL.",
        )

    result, chunk_count = await analyze_text_with_metadata(body_text, already_cleaned=True)
    response = URLAnalysisResult(
        url=url_str,
        title=title,
        result=result,
        chunk_count=chunk_count,
    )
    await cache_set(cache_key, response.model_dump_json(), CACHE_TTL_SECONDS)
    return response
