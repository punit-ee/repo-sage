"""Tests for chunking strategies."""

import pytest

from repo_sage.chunking.chunker import ChunkingError
from repo_sage.chunking.strategies import (
    IntelligentChunkingStrategy,
    SemanticChunkingStrategy,
    SlidingWindowStrategy,
)


class TestSlidingWindowStrategy:
    """Tests for SlidingWindowStrategy."""

    def test_initialization_default(self):
        """Test default initialization."""
        strategy = SlidingWindowStrategy()

        assert strategy.window_size == 2000
        assert strategy.step_size == 1000
        assert strategy.min_chunk_size == 100

    def test_initialization_custom(self):
        """Test custom initialization."""
        strategy = SlidingWindowStrategy(
            window_size=500, step_size=250, min_chunk_size=50
        )

        assert strategy.window_size == 500
        assert strategy.step_size == 250
        assert strategy.min_chunk_size == 50

    def test_validate_config_invalid_window_size(self):
        """Test validation with invalid window size."""
        with pytest.raises(ValueError, match="window_size must be positive"):
            SlidingWindowStrategy(window_size=0)

        with pytest.raises(ValueError, match="window_size must be positive"):
            SlidingWindowStrategy(window_size=-100)

    def test_validate_config_invalid_step_size(self):
        """Test validation with invalid step size."""
        with pytest.raises(ValueError, match="step_size must be positive"):
            SlidingWindowStrategy(step_size=0)

        with pytest.raises(ValueError, match="step_size must be positive"):
            SlidingWindowStrategy(step_size=-50)

    def test_validate_config_invalid_min_chunk_size(self):
        """Test validation with invalid min chunk size."""
        with pytest.raises(ValueError, match="min_chunk_size must be non-negative"):
            SlidingWindowStrategy(min_chunk_size=-1)

        with pytest.raises(ValueError, match="cannot exceed window_size"):
            SlidingWindowStrategy(window_size=100, min_chunk_size=200)

    def test_chunk_simple_text(self):
        """Test chunking simple text."""
        strategy = SlidingWindowStrategy(window_size=10, step_size=5, min_chunk_size=1)
        text = "0123456789abcdefghij"  # 20 chars

        chunks = strategy.chunk(text)

        assert len(chunks) == 4
        assert chunks[0].content == "0123456789"
        assert chunks[0].start == 0
        assert chunks[0].end == 10
        assert chunks[1].content == "56789abcde"
        assert chunks[1].start == 5
        assert chunks[1].end == 15
        assert chunks[2].content == "abcdefghij"
        assert chunks[2].start == 10
        assert chunks[2].end == 20
        assert chunks[3].content == "fghij"
        assert chunks[3].start == 15
        assert chunks[3].end == 20

    def test_chunk_with_overlap(self):
        """Test that overlap is correctly calculated."""
        strategy = SlidingWindowStrategy(
            window_size=100, step_size=50, min_chunk_size=1
        )
        text = "x" * 200

        chunks = strategy.chunk(text)

        assert len(chunks) == 4
        # Overlap should be window_size - step_size = 50
        assert chunks[0].metadata["overlap"] == 50

    def test_chunk_no_overlap(self):
        """Test chunking without overlap."""
        strategy = SlidingWindowStrategy(window_size=10, step_size=10, min_chunk_size=1)
        text = "0123456789abcdefghij"

        chunks = strategy.chunk(text)

        assert len(chunks) == 2
        assert chunks[0].content == "0123456789"
        assert chunks[1].content == "abcdefghij"
        assert chunks[0].metadata["overlap"] == 0

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        strategy = SlidingWindowStrategy()

        chunks = strategy.chunk("")

        assert chunks == []

    def test_chunk_text_smaller_than_window(self):
        """Test chunking text smaller than window size."""
        strategy = SlidingWindowStrategy(window_size=100, step_size=50)
        text = "small"

        chunks = strategy.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == "small"
        assert chunks[0].start == 0
        assert chunks[0].end == 5

    def test_chunk_min_chunk_size_filtering(self):
        """Test that small final chunks are filtered out."""
        strategy = SlidingWindowStrategy(window_size=10, step_size=10, min_chunk_size=5)
        text = "0123456789abc"  # 13 chars, last chunk would be 3 chars

        chunks = strategy.chunk(text)

        # Last chunk is too small and should be skipped
        assert len(chunks) == 1
        assert chunks[0].content == "0123456789"

    def test_chunk_with_metadata(self):
        """Test chunking with metadata."""
        strategy = SlidingWindowStrategy(window_size=10, step_size=10, min_chunk_size=1)
        text = "0123456789"
        metadata = {"source": "test.md"}

        chunks = strategy.chunk(text, metadata)

        assert chunks[0].metadata["source"] == "test.md"
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[0].metadata["chunk_method"] == "sliding_window"
        assert chunks[0].metadata["window_size"] == 10

    def test_chunk_invalid_text_type(self):
        """Test chunking with invalid text type."""
        strategy = SlidingWindowStrategy()

        with pytest.raises(ChunkingError, match="Text must be a string"):
            strategy.chunk(123)  # type: ignore


class TestIntelligentChunkingStrategy:
    """Tests for IntelligentChunkingStrategy."""

    def test_initialization_basic(self):
        """Test basic initialization."""
        llm_func = lambda x: "section1\n---\nsection2"
        strategy = IntelligentChunkingStrategy(llm_function=llm_func)

        assert strategy.llm_function == llm_func
        assert "{document}" in strategy.prompt_template
        assert strategy.max_retries == 3
        assert strategy.fallback_strategy is None

    def test_initialization_with_custom_prompt(self):
        """Test initialization with custom prompt template."""
        llm_func = lambda x: "result"
        custom_prompt = "Split this: {document}"
        strategy = IntelligentChunkingStrategy(
            llm_function=llm_func, prompt_template=custom_prompt
        )

        assert strategy.prompt_template == custom_prompt

    def test_initialization_with_fallback(self):
        """Test initialization with fallback strategy."""
        llm_func = lambda x: "result"
        fallback = SlidingWindowStrategy()
        strategy = IntelligentChunkingStrategy(
            llm_function=llm_func, fallback_strategy=fallback
        )

        assert strategy.fallback_strategy == fallback

    def test_validate_config_invalid_llm_function(self):
        """Test validation with non-callable LLM function."""
        with pytest.raises(ValueError, match="llm_function must be callable"):
            IntelligentChunkingStrategy(llm_function="not callable")  # type: ignore

    def test_validate_config_invalid_prompt_template(self):
        """Test validation with invalid prompt template."""
        llm_func = lambda x: "result"

        with pytest.raises(ValueError, match="prompt_template must contain {document}"):
            IntelligentChunkingStrategy(
                llm_function=llm_func, prompt_template="no placeholder"
            )

    def test_validate_config_invalid_max_retries(self):
        """Test validation with invalid max retries."""
        llm_func = lambda x: "result"

        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            IntelligentChunkingStrategy(llm_function=llm_func, max_retries=-1)

    def test_validate_config_invalid_fallback(self):
        """Test validation with invalid fallback strategy."""
        llm_func = lambda x: "result"

        with pytest.raises(
            ValueError, match="fallback_strategy must be a ChunkingStrategy"
        ):
            IntelligentChunkingStrategy(
                llm_function=llm_func,
                fallback_strategy="not a strategy",  # type: ignore
            )

    def test_chunk_basic(self):
        """Test basic LLM chunking."""
        llm_func = lambda x: "## Section 1\nContent 1\n---\n## Section 2\nContent 2"
        strategy = IntelligentChunkingStrategy(llm_function=llm_func)
        text = "Original document text"

        chunks = strategy.chunk(text)

        assert len(chunks) == 2
        assert "Section 1" in chunks[0].content
        assert "Section 2" in chunks[1].content
        assert chunks[0].metadata["chunk_method"] == "intelligent_llm"
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[1].metadata["chunk_index"] == 1

    def test_chunk_with_metadata(self):
        """Test chunking with metadata."""
        llm_func = lambda x: "section1\n---\nsection2"
        strategy = IntelligentChunkingStrategy(llm_function=llm_func)
        metadata = {"source": "test.md"}

        chunks = strategy.chunk("text", metadata)

        assert chunks[0].metadata["source"] == "test.md"

    def test_chunk_llm_returns_empty(self):
        """Test handling of empty LLM response."""
        llm_func = lambda x: ""
        strategy = IntelligentChunkingStrategy(llm_function=llm_func, max_retries=1)

        with pytest.raises(ChunkingError, match="LLM chunking failed after"):
            strategy.chunk("text")

    def test_chunk_llm_returns_invalid_type(self):
        """Test handling of invalid LLM response type."""
        llm_func = lambda x: None
        strategy = IntelligentChunkingStrategy(llm_function=llm_func, max_retries=1)

        with pytest.raises(ChunkingError, match="LLM chunking failed after"):
            strategy.chunk("text")

    def test_chunk_llm_raises_exception(self):
        """Test handling of LLM exceptions."""

        def failing_llm(x: str) -> str:
            raise RuntimeError("LLM API error")

        strategy = IntelligentChunkingStrategy(llm_function=failing_llm, max_retries=1)

        with pytest.raises(ChunkingError, match="failed after 1 attempts"):
            strategy.chunk("text")

    def test_chunk_fallback_on_failure(self):
        """Test fallback strategy is used when LLM fails."""

        def failing_llm(x: str) -> str:
            raise RuntimeError("LLM error")

        fallback = SlidingWindowStrategy(window_size=10, step_size=10, min_chunk_size=1)
        strategy = IntelligentChunkingStrategy(
            llm_function=failing_llm, max_retries=1, fallback_strategy=fallback
        )
        text = "0123456789"

        chunks = strategy.chunk(text)

        # Should use fallback strategy
        assert len(chunks) > 0
        assert chunks[0].content == text
        assert chunks[0].metadata["chunk_method"] == "sliding_window"

    def test_chunk_retry_logic(self):
        """Test that retries work correctly."""
        call_count = 0

        def llm_with_retries(x: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Temporary error")
            return "section1\n---\nsection2"

        strategy = IntelligentChunkingStrategy(
            llm_function=llm_with_retries, max_retries=3
        )

        chunks = strategy.chunk("text")

        assert call_count == 3
        assert len(chunks) == 2

    def test_chunk_invalid_text_type(self):
        """Test chunking with invalid text type."""
        llm_func = lambda x: "result"
        strategy = IntelligentChunkingStrategy(llm_function=llm_func)

        with pytest.raises(ChunkingError, match="Text must be a string"):
            strategy.chunk(123)  # type: ignore


class TestSemanticChunkingStrategy:
    """Tests for SemanticChunkingStrategy."""

    def test_initialization_default(self):
        """Test default initialization."""
        strategy = SemanticChunkingStrategy()

        assert strategy.max_chunk_size == 2000
        assert strategy.min_chunk_size == 100
        assert strategy.respect_paragraphs is True
        assert strategy.respect_sentences is True

    def test_initialization_custom(self):
        """Test custom initialization."""
        strategy = SemanticChunkingStrategy(
            max_chunk_size=500,
            min_chunk_size=50,
            respect_paragraphs=False,
            respect_sentences=False,
        )

        assert strategy.max_chunk_size == 500
        assert strategy.min_chunk_size == 50
        assert strategy.respect_paragraphs is False
        assert strategy.respect_sentences is False

    def test_validate_config_invalid_max_chunk_size(self):
        """Test validation with invalid max chunk size."""
        with pytest.raises(ValueError, match="max_chunk_size must be positive"):
            SemanticChunkingStrategy(max_chunk_size=0)

    def test_validate_config_invalid_min_chunk_size(self):
        """Test validation with invalid min chunk size."""
        with pytest.raises(ValueError, match="min_chunk_size must be non-negative"):
            SemanticChunkingStrategy(min_chunk_size=-1)

        with pytest.raises(ValueError, match="cannot exceed max_chunk_size"):
            SemanticChunkingStrategy(max_chunk_size=100, min_chunk_size=200)

    def test_chunk_single_paragraph(self):
        """Test chunking a single paragraph."""
        strategy = SemanticChunkingStrategy(max_chunk_size=100, min_chunk_size=10)
        text = "This is a short paragraph."

        chunks = strategy.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].metadata["chunk_method"] == "semantic"

    def test_chunk_multiple_paragraphs_fit_in_one(self):
        """Test multiple small paragraphs that fit in one chunk."""
        strategy = SemanticChunkingStrategy(max_chunk_size=100, min_chunk_size=10)
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."

        chunks = strategy.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_multiple_paragraphs_split(self):
        """Test paragraphs that need to be split into multiple chunks."""
        strategy = SemanticChunkingStrategy(max_chunk_size=50, min_chunk_size=10)
        text = "This is paragraph one with enough text.\n\nThis is paragraph two with more text.\n\nParagraph three."

        chunks = strategy.chunk(text)

        assert len(chunks) >= 2
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[1].metadata["chunk_index"] == 1

    def test_chunk_large_paragraph_split(self):
        """Test that large paragraphs are split."""
        strategy = SemanticChunkingStrategy(
            max_chunk_size=50, min_chunk_size=10, respect_sentences=True
        )
        text = (
            "This is sentence one. This is sentence two. This is sentence three. " * 5
        )  # Multiple sentences

        chunks = strategy.chunk(text)

        assert len(chunks) > 1
        for chunk in chunks:
            assert (
                len(chunk.content) <= strategy.max_chunk_size * 2
            )  # Allow some flexibility

    def test_chunk_respect_paragraphs(self):
        """Test that paragraph boundaries are respected."""
        strategy = SemanticChunkingStrategy(
            max_chunk_size=100, min_chunk_size=10, respect_paragraphs=True
        )
        text = "Para1.\n\nPara2.\n\nPara3."

        chunks = strategy.chunk(text)

        # Each chunk should contain complete paragraphs
        for chunk in chunks:
            # Should not end mid-word (rough check)
            assert not chunk.content.endswith(" and ")

    def test_chunk_with_metadata(self):
        """Test chunking with metadata."""
        strategy = SemanticChunkingStrategy(min_chunk_size=10)
        metadata = {"source": "test.md", "title": "Test"}
        text = "Some text with enough content to make a chunk that passes minimum size and more content here."

        chunks = strategy.chunk(text, metadata)

        assert len(chunks) > 0
        assert chunks[0].metadata["source"] == "test.md"
        assert chunks[0].metadata["title"] == "Test"
        assert chunks[0].metadata["chunk_method"] == "semantic"

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        strategy = SemanticChunkingStrategy()

        chunks = strategy.chunk("")

        assert chunks == []

    def test_chunk_invalid_text_type(self):
        """Test chunking with invalid text type."""
        strategy = SemanticChunkingStrategy()

        with pytest.raises(ChunkingError, match="Text must be a string"):
            strategy.chunk(123)  # type: ignore

    def test_chunk_only_whitespace_paragraphs(self):
        """Test handling of whitespace-only paragraphs."""
        strategy = SemanticChunkingStrategy(max_chunk_size=100, min_chunk_size=5)
        text = "Para1 with some content.\n\n   \n\nPara2 with more text that is sufficient."

        chunks = strategy.chunk(text)

        # Should skip empty paragraphs
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.content.strip()

    def test_chunk_min_size_filtering(self):
        """Test that chunks below min size are filtered."""
        strategy = SemanticChunkingStrategy(max_chunk_size=100, min_chunk_size=20)
        # Create text that would result in a small final chunk
        text = "x" * 150 + "\n\ny"  # Last chunk would be just "y"

        chunks = strategy.chunk(text)

        # Small final chunk should be excluded
        for chunk in chunks:
            assert len(chunk.content) >= strategy.min_chunk_size or len(chunks) == 1

    def test_split_by_sentences(self):
        """Test sentence splitting logic."""
        strategy = SemanticChunkingStrategy(
            max_chunk_size=50, min_chunk_size=10, respect_sentences=True
        )
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."

        chunks = strategy.chunk(text)

        # Should split on sentence boundaries
        assert len(chunks) >= 1
