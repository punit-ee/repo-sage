"""Tests for core chunking functionality."""

import pytest

from repo_sage.chunking.chunker import (
    Chunk,
    ChunkingError,
    ChunkingStrategy,
    DocumentChunker,
)


class TestChunk:
    """Tests for Chunk class."""

    def test_chunk_initialization(self):
        """Test basic chunk creation."""
        chunk = Chunk(content="test content", start=0, end=12)

        assert chunk.content == "test content"
        assert chunk.start == 0
        assert chunk.end == 12
        assert chunk.metadata == {}

    def test_chunk_with_metadata(self):
        """Test chunk creation with metadata."""
        metadata = {"source": "test.md", "author": "John"}
        chunk = Chunk(content="test", start=0, end=4, metadata=metadata)

        assert chunk.metadata == metadata

    def test_chunk_invalid_content(self):
        """Test chunk creation with invalid content type."""
        with pytest.raises(ValueError, match="content must be a string"):
            Chunk(content=123, start=0, end=3)  # type: ignore

    def test_chunk_invalid_boundaries(self):
        """Test chunk creation with invalid boundaries."""
        with pytest.raises(ValueError, match="Invalid chunk boundaries"):
            Chunk(content="test", start=-1, end=4)

        with pytest.raises(ValueError, match="Invalid chunk boundaries"):
            Chunk(content="test", start=10, end=4)

    def test_chunk_to_dict(self):
        """Test chunk conversion to dictionary."""
        metadata = {"key": "value"}
        chunk = Chunk(content="test", start=0, end=4, metadata=metadata)

        result = chunk.to_dict()

        assert result == {
            "content": "test",
            "start": 0,
            "end": 4,
            "metadata": {"key": "value"},
        }

    def test_chunk_repr(self):
        """Test chunk string representation."""
        chunk = Chunk(content="test content", start=0, end=12)

        repr_str = repr(chunk)

        assert "start=0" in repr_str
        assert "end=12" in repr_str
        assert "length=12" in repr_str

    def test_chunk_equality(self):
        """Test chunk equality comparison."""
        chunk1 = Chunk(content="test", start=0, end=4, metadata={"key": "value"})
        chunk2 = Chunk(content="test", start=0, end=4, metadata={"key": "value"})
        chunk3 = Chunk(content="test", start=0, end=4, metadata={"key": "other"})

        assert chunk1 == chunk2
        assert chunk1 != chunk3
        assert chunk1 != "not a chunk"


class MockChunkingStrategy(ChunkingStrategy):
    """Mock strategy for testing."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.chunk_called = False

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        self.chunk_called = True
        if self.should_fail:
            raise ValueError("Mock failure")
        return [Chunk(content=text, start=0, end=len(text), metadata=metadata)]

    def validate_config(self) -> None:
        pass


class TestDocumentChunker:
    """Tests for DocumentChunker class."""

    def test_chunker_initialization(self):
        """Test chunker initialization with valid strategy."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        assert chunker.strategy == strategy

    def test_chunker_initialization_invalid_strategy(self):
        """Test chunker initialization with invalid strategy."""
        with pytest.raises(TypeError, match="must be an instance of ChunkingStrategy"):
            DocumentChunker("not a strategy")  # type: ignore

    def test_set_strategy(self):
        """Test changing the chunking strategy."""
        strategy1 = MockChunkingStrategy()
        strategy2 = MockChunkingStrategy()
        chunker = DocumentChunker(strategy1)

        chunker.set_strategy(strategy2)

        assert chunker.strategy == strategy2

    def test_set_strategy_invalid(self):
        """Test setting invalid strategy."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        with pytest.raises(TypeError, match="must be an instance of ChunkingStrategy"):
            chunker.set_strategy("not a strategy")  # type: ignore

    def test_chunk_document_basic(self):
        """Test basic document chunking."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        result = chunker.chunk_document("test content")

        assert len(result) == 1
        assert result[0].content == "test content"
        assert strategy.chunk_called

    def test_chunk_document_with_metadata(self):
        """Test document chunking with metadata."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)
        metadata = {"source": "test.md"}

        result = chunker.chunk_document("test", metadata)

        assert result[0].metadata == metadata

    def test_chunk_document_invalid_text(self):
        """Test chunking with invalid text type."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        with pytest.raises(ChunkingError, match="must be a string"):
            chunker.chunk_document(123)  # type: ignore

    def test_chunk_document_empty_text(self):
        """Test chunking empty text."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        result = chunker.chunk_document("")

        assert result == []

    def test_chunk_document_whitespace_only(self):
        """Test chunking whitespace-only text."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        result = chunker.chunk_document("   \n\t  ")

        assert result == []

    def test_chunk_document_strategy_failure(self):
        """Test handling of strategy failures."""
        strategy = MockChunkingStrategy(should_fail=True)
        chunker = DocumentChunker(strategy)

        with pytest.raises(ChunkingError, match="Failed to chunk document"):
            chunker.chunk_document("test")

    def test_chunk_documents_basic(self):
        """Test chunking multiple documents."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)
        documents = [
            {"content": "doc1", "title": "Title 1"},
            {"content": "doc2", "title": "Title 2"},
        ]

        result = chunker.chunk_documents(documents)

        assert len(result) == 2
        assert result[0].content == "doc1"
        assert result[0].metadata["title"] == "Title 1"
        assert result[0].metadata["document_index"] == 0
        assert result[1].content == "doc2"
        assert result[1].metadata["title"] == "Title 2"
        assert result[1].metadata["document_index"] == 1

    def test_chunk_documents_custom_content_field(self):
        """Test chunking with custom content field name."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)
        documents = [{"text": "doc1", "title": "Title 1"}]

        result = chunker.chunk_documents(documents, content_field="text")

        assert len(result) == 1
        assert result[0].content == "doc1"
        assert "text" not in result[0].metadata
        assert result[0].metadata["title"] == "Title 1"

    def test_chunk_documents_invalid_input(self):
        """Test chunking with invalid documents input."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        with pytest.raises(ChunkingError, match="must be a list"):
            chunker.chunk_documents("not a list")  # type: ignore

    def test_chunk_documents_skip_invalid_documents(self):
        """Test that invalid documents are skipped."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)
        documents = [
            {"content": "valid"},
            "invalid",
            {"content": "also valid"},
            {"no_content": "missing content"},
            {"content": 123},  # invalid content type
        ]

        result = chunker.chunk_documents(documents)

        # Only 2 valid documents should be processed
        assert len(result) == 2
        assert result[0].content == "valid"
        assert result[1].content == "also valid"

    def test_chunk_documents_empty_list(self):
        """Test chunking empty document list."""
        strategy = MockChunkingStrategy()
        chunker = DocumentChunker(strategy)

        result = chunker.chunk_documents([])

        assert result == []

    def test_chunk_documents_strategy_failure_continues(self):
        """Test that failures on individual documents don't stop processing."""

        # Create a strategy that fails on specific text
        class SelectiveFailStrategy(ChunkingStrategy):
            def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
                if text == "fail":
                    raise ValueError("Intentional failure")
                return [Chunk(content=text, start=0, end=len(text), metadata=metadata)]

            def validate_config(self) -> None:
                pass

        strategy = SelectiveFailStrategy()
        chunker = DocumentChunker(strategy)
        documents = [
            {"content": "good1"},
            {"content": "fail"},
            {"content": "good2"},
        ]

        result = chunker.chunk_documents(documents)

        # Should have 2 successful chunks
        assert len(result) == 2
        assert result[0].content == "good1"
        assert result[1].content == "good2"
