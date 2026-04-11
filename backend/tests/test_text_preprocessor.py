from __future__ import annotations

from app.ml.text_preprocessor import chunk_text, clean_text


class TestCleanText:
    def test_strips_html_tags(self) -> None:
        result = clean_text("<p>Hello <b>world</b></p>")
        assert "<" not in result
        assert "Hello" in result
        assert "world" in result

    def test_normalises_whitespace(self) -> None:
        result = clean_text("Hello   \n\n  world")
        assert "  " not in result
        assert result.strip() == result

    def test_truncates_to_5000_chars(self) -> None:
        long_text = "a" * 6000
        result = clean_text(long_text)
        assert len(result) <= 5000

    def test_empty_string_returns_empty(self) -> None:
        assert clean_text("") == ""

    def test_plain_text_unchanged(self) -> None:
        text = "The quick brown fox jumps over the lazy dog."
        result = clean_text(text)
        assert "quick brown fox" in result

    def test_strips_urls(self) -> None:
        text = "Read more at https://example.com/article and visit http://test.org"
        result = clean_text(text)
        assert "https://" not in result
        assert "Read more" in result


class TestChunkText:
    def test_short_text_returns_single_chunk(self) -> None:
        text = "This is a short sentence."
        chunks = chunk_text(text, chunk_size=400, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_splits_into_multiple_chunks(self) -> None:
        words = ["word"] * 900
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=400, overlap=50)
        assert len(chunks) >= 2

    def test_chunks_have_overlap(self) -> None:
        words = [f"w{i}" for i in range(500)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=200, overlap=50)
        if len(chunks) >= 2:
            chunk0_words = set(chunks[0].split()[-60:])
            chunk1_words = set(chunks[1].split()[:60])
            assert len(chunk0_words & chunk1_words) > 0

    def test_no_chunk_exceeds_chunk_size_words(self) -> None:
        words = ["word"] * 1000
        text = " ".join(words)
        chunk_size = 200
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=20)
        for chunk in chunks:
            assert len(chunk.split()) <= chunk_size + 20

    def test_empty_string_returns_empty_list_or_single_empty(self) -> None:
        chunks = chunk_text("", chunk_size=400, overlap=50)
        assert chunks == [] or chunks == [""]
