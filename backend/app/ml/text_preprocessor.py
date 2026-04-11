import re

from app.ml.model_config import MAX_TOKENS

HTML_TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+|www\.\S+")
WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    cleaned = HTML_TAG_RE.sub(" ", text)
    cleaned = URL_RE.sub(" ", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned[:5000]


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    effective_chunk_size = min(chunk_size, MAX_TOKENS)
    if len(words) <= effective_chunk_size:
        return [" ".join(words)]

    step = max(effective_chunk_size - overlap, 1)
    chunks: list[str] = []

    for start in range(0, len(words), step):
        chunk_words = words[start : start + effective_chunk_size]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
        if start + effective_chunk_size >= len(words):
            break

    return chunks
