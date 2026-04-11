from __future__ import annotations

import logging
import time
from typing import Any

from transformers import pipeline

from app.core.config import settings

logger = logging.getLogger(__name__)
_pipeline: Any | None = None


def load_pipeline() -> Any:
    global _pipeline
    if _pipeline is None:
        started_at = time.perf_counter()
        _pipeline = pipeline(
            "text-classification",
            model=settings.MODEL_NAME,
            top_k=None,
            device=-1,
        )
        elapsed = time.perf_counter() - started_at
        logger.info(
            "Loaded sentiment pipeline model=%s in %.2f seconds",
            settings.MODEL_NAME,
            elapsed,
        )
    return _pipeline


def get_pipeline() -> Any:
    if _pipeline is None:
        raise RuntimeError("Sentiment pipeline has not been loaded yet")
    return _pipeline


def is_pipeline_loaded() -> bool:
    return _pipeline is not None
