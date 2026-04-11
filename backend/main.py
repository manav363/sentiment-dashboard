import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import uuid4

import uvicorn
from app.api import sentiment, url_scraper
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.core.request_context import reset_request_id, set_request_id
from app.ml.pipeline_loader import is_pipeline_loaded, load_pipeline
from app.services.cache_service import get_redis, redis_connected
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Loading sentiment pipeline…")
    await asyncio.to_thread(load_pipeline)
    logger.info("Pipeline ready.")
    yield
    try:
        redis = get_redis()
        await redis.aclose()
    except Exception:
        pass


app = FastAPI(
    title="Sentiment Analysis API",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])
app.include_router(url_scraper.router, prefix="/api/url", tags=["url"])


@app.get("/health")
async def health_check() -> dict[str, bool | str]:
    return {
        "status": "ok",
        "model_loaded": is_pipeline_loaded(),
        "redis_connected": await redis_connected(),
    }


MAX_BODY_SIZE = 65_536  # 64 KB


@app.middleware("http")
async def enforce_body_size_limit(request: Request, call_next) -> Response:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return Response(
            content='{"detail":"Request body too large"}',
            status_code=413,
            media_type="application/json",
        )
    return await call_next(request)


@app.middleware("http")
async def add_request_id(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    token = set_request_id(request_id)
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled request error request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        raise
    finally:
        reset_request_id(token)
    response.headers["X-Request-ID"] = request_id
    return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=False)
