from hashlib import sha256

from fastapi import APIRouter, Request

from app.core.rate_limiter import SENTIMENT_LIMIT, limiter
from app.ml.model_config import CACHE_TTL_SECONDS
from app.models.request import AnalyzeTextRequest
from app.models.response import SentimentResult
from app.services.cache_service import cache_get, cache_set
from app.services.sentiment_engine import analyze_text

router = APIRouter()


@router.post("/analyze", response_model=SentimentResult)
@limiter.limit(SENTIMENT_LIMIT)
async def analyze_sentiment(request: Request, payload: AnalyzeTextRequest) -> SentimentResult:  # noqa: ARG001 — required by @limiter.limit
    cache_key = f"sentiment:text:{sha256(payload.text.encode('utf-8')).hexdigest()}"
    cached = await cache_get(cache_key)
    if cached:
        return SentimentResult.model_validate_json(cached)

    result = await analyze_text(payload.text)
    await cache_set(cache_key, result.model_dump_json(), CACHE_TTL_SECONDS)
    return result
