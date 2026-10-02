from __future__ import annotations

import asyncio
import logging

from app.core.request_context import get_request_id
from app.ml.model_config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    INFERENCE_CONCURRENCY,
    LABELS,
    MAX_TOKENS,
)
from app.ml.pipeline_loader import get_pipeline
from app.ml.text_preprocessor import chunk_text, clean_text
from app.models.response import ScoreBreakdown, SentimentResult

logger = logging.getLogger(__name__)

MODEL_LABEL_MAP = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
}


def _normalize_scores(
    raw_output: list[dict[str, float]] | list[list[dict[str, float]]],
) -> dict[str, float]:
    scores = raw_output[0] if raw_output and isinstance(raw_output[0], list) else raw_output
    mapped = {label: 0.0 for label in LABELS}

    for item in scores:
        mapped[MODEL_LABEL_MAP.get(item["label"], item["label"].lower())] = float(item["score"])

    return mapped


async def _run_inference(text: str) -> dict[str, float]:
    try:
        pipeline = get_pipeline()
        # Chunks are sized in words, and a 400-word chunk can exceed the model's 512-token
        # window; without truncation the tokenizer output would be too long for the model.
        output = await asyncio.to_thread(pipeline, text, truncation=True, max_length=MAX_TOKENS)
    except Exception:
        logger.exception(
            "Sentiment inference failed request_id=%s text_length=%s",
            get_request_id(),
            len(text),
        )
        raise
    return _normalize_scores(output)


async def _run_chunk_inference(
    chunk: str,
    index: int,
    total_chunks: int,
    semaphore: asyncio.Semaphore,
) -> dict[str, float]:
    async with semaphore:
        logger.info(
            "Processing chunk request_id=%s chunk=%s/%s chunk_length=%s",
            get_request_id(),
            index,
            total_chunks,
            len(chunk),
        )
        return await _run_inference(chunk)


async def analyze_text_with_metadata(
    text: str,
    *,
    already_cleaned: bool = False,
) -> tuple[SentimentResult, int]:
    cleaned = text if already_cleaned else clean_text(text)
    chunks = chunk_text(cleaned, CHUNK_SIZE, CHUNK_OVERLAP)
    chunk_count = max(len(chunks), 1)
    logger.info(
        "Starting sentiment analysis request_id=%s text_length=%s chunk_count=%s",
        get_request_id(),
        len(cleaned),
        chunk_count,
    )

    if len(chunks) > 1:
        semaphore = asyncio.Semaphore(INFERENCE_CONCURRENCY)
        chunk_scores = await asyncio.gather(
            *(
                _run_chunk_inference(chunk, index, len(chunks), semaphore)
                for index, chunk in enumerate(chunks, start=1)
            )
        )
        averaged_scores = {
            label: sum(item[label] for item in chunk_scores) / len(chunk_scores) for label in LABELS
        }
    else:
        target_text = chunks[0] if chunks else cleaned
        averaged_scores = await _run_inference(target_text)

    breakdown = [
        ScoreBreakdown(label=label, score=averaged_scores[label])
        for label in ["positive", "neutral", "negative"]
    ]
    dominant = max(breakdown, key=lambda item: item.score)

    result = SentimentResult(
        label=dominant.label,
        score=dominant.score,
        breakdown=breakdown,
        text_preview=cleaned[:200],
    )
    logger.info(
        "Completed sentiment analysis request_id=%s label=%s score=%.4f chunk_count=%s",
        get_request_id(),
        result.label,
        result.score,
        chunk_count,
    )
    return result, chunk_count


async def analyze_text(text: str, *, already_cleaned: bool = False) -> SentimentResult:
    result, _ = await analyze_text_with_metadata(text, already_cleaned=already_cleaned)
    return result
