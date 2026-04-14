"""Integration tests for chunking with GitHub reader."""

from repo_sage.chunking import (
    DocumentChunker,
    IntelligentChunkingStrategy,
    SemanticChunkingStrategy,
    SlidingWindowStrategy,
)


class TestChunkingIntegration:
    """Integration tests for chunking functionality."""

    def test_sliding_window_on_documents(self):
        """Test sliding window chunking on document-like data."""
        # Simulate documents from GitHub reader
        documents = [
            {
                "content": "x" * 300,
                "filename": "test1.md",
                "title": "Document 1",
            },
            {
                "content": "y" * 250,
                "filename": "test2.md",
                "title": "Document 2",
            },
        ]

        strategy = SlidingWindowStrategy(
            window_size=100, step_size=50, min_chunk_size=25
        )
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)

        # Verify chunks were created
        assert len(chunks) > 0

        # Verify metadata is preserved
        assert any(chunk.metadata.get("filename") == "test1.md" for chunk in chunks)
        assert any(chunk.metadata.get("filename") == "test2.md" for chunk in chunks)

        # Verify chunk metadata
        for chunk in chunks:
            assert "chunk_index" in chunk.metadata
            assert "chunk_method" in chunk.metadata
            assert chunk.metadata["chunk_method"] == "sliding_window"

    def test_semantic_chunking_on_markdown(self):
        """Test semantic chunking on markdown-like content."""
        documents = [
            {
                "content": """# Introduction

This is the introduction paragraph with some content.

## Section 1

This is section 1 with more detailed information.

## Section 2

This is section 2 with even more information.

## Conclusion

Final thoughts and summary.""",
                "filename": "readme.md",
            }
        ]

        strategy = SemanticChunkingStrategy(max_chunk_size=100, min_chunk_size=20)
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Verify chunks respect paragraph boundaries
        for chunk in chunks:
            assert "\n\n" in chunk.content or len(chunk.content) < 100

    def test_intelligent_chunking_with_mock_llm(self):
        """Test intelligent chunking with a mock LLM."""

        def mock_llm(prompt: str) -> str:
            """Mock LLM that returns predefined sections."""
            return """## Introduction Section

This is the introduction with key concepts.

---

## Main Content Section

This is the main content with details.

---

## Conclusion Section

This is the conclusion and summary."""

        documents = [
            {
                "content": "Some long document that needs intelligent splitting",
                "filename": "doc.md",
            }
        ]

        strategy = IntelligentChunkingStrategy(llm_function=mock_llm)
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)

        # Should have 3 sections
        assert len(chunks) == 3
        assert "Introduction" in chunks[0].content
        assert "Main Content" in chunks[1].content
        assert "Conclusion" in chunks[2].content

    def test_intelligent_chunking_with_fallback(self):
        """Test intelligent chunking falls back when LLM fails."""

        def failing_llm(prompt: str) -> str:
            raise RuntimeError("LLM service unavailable")

        fallback = SlidingWindowStrategy(
            window_size=50, step_size=25, min_chunk_size=10
        )
        strategy = IntelligentChunkingStrategy(
            llm_function=failing_llm, max_retries=1, fallback_strategy=fallback
        )

        documents = [
            {"content": "x" * 100, "filename": "test.md"},
        ]

        chunker = DocumentChunker(strategy)
        chunks = chunker.chunk_documents(documents)

        # Should use fallback strategy
        assert len(chunks) > 0
        assert chunks[0].metadata["chunk_method"] == "sliding_window"

    def test_strategy_switching(self):
        """Test switching strategies mid-processing."""
        document = {"content": "x" * 200, "filename": "test.md"}

        # Start with sliding window
        strategy1 = SlidingWindowStrategy(window_size=100, step_size=100)
        chunker = DocumentChunker(strategy1)
        chunks1 = chunker.chunk_documents([document])

        # Switch to semantic chunking
        strategy2 = SemanticChunkingStrategy(max_chunk_size=100)
        chunker.set_strategy(strategy2)
        chunks2 = chunker.chunk_documents([document])

        # Results should differ
        assert chunks1[0].metadata["chunk_method"] == "sliding_window"
        assert chunks2[0].metadata["chunk_method"] == "semantic"

    def test_empty_documents_handling(self):
        """Test handling of empty documents."""
        documents = [
            {"content": "", "filename": "empty.md"},
            {"content": "   \n\n   ", "filename": "whitespace.md"},
            {"content": "valid content", "filename": "valid.md"},
        ]

        strategy = SlidingWindowStrategy()
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)

        # Only valid document should produce chunks
        assert len(chunks) >= 1
        assert any(chunk.metadata.get("filename") == "valid.md" for chunk in chunks)

    def test_large_document_processing(self):
        """Test processing of large documents."""
        # Create a large document
        large_content = "\n\n".join(
            [f"Paragraph {i} with some content." for i in range(100)]
        )

        documents = [
            {"content": large_content, "filename": "large.md"},
        ]

        strategy = SlidingWindowStrategy(window_size=500, step_size=250)
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)

        # Should create multiple chunks
        assert len(chunks) > 5

        # Verify overlap
        for i in range(len(chunks) - 1):
            # There should be some overlap between consecutive chunks
            assert chunks[i].metadata["overlap"] > 0

    def test_metadata_preservation(self):
        """Test that document metadata is preserved in chunks."""
        documents = [
            {
                "content": "Content here",
                "filename": "test.md",
                "author": "John Doe",
                "date": "2024-01-01",
                "tags": ["python", "testing"],
                "nested": {"key": "value"},
            }
        ]

        strategy = SlidingWindowStrategy()
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)

        # All metadata should be preserved
        assert chunks[0].metadata["filename"] == "test.md"
        assert chunks[0].metadata["author"] == "John Doe"
        assert chunks[0].metadata["date"] == "2024-01-01"
        assert chunks[0].metadata["tags"] == ["python", "testing"]
        assert chunks[0].metadata["nested"]["key"] == "value"

    def test_mixed_document_types(self):
        """Test processing documents with different characteristics."""
        documents = [
            {"content": "Short doc", "type": "short"},
            {"content": "x" * 5000, "type": "long"},
            {"content": "Medium " * 50, "type": "medium"},
        ]

        strategy = SlidingWindowStrategy(window_size=1000, step_size=500)
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)

        # Verify different documents produce different numbers of chunks
        short_chunks = [c for c in chunks if c.metadata.get("type") == "short"]
        long_chunks = [c for c in chunks if c.metadata.get("type") == "long"]

        assert len(short_chunks) < len(long_chunks)

    def test_chunk_to_dict_conversion(self):
        """Test converting chunks to dictionaries for storage/API."""
        documents = [
            {"content": "Test content", "filename": "test.md"},
        ]

        strategy = SlidingWindowStrategy()
        chunker = DocumentChunker(strategy)

        chunks = chunker.chunk_documents(documents)
        chunk_dicts = [chunk.to_dict() for chunk in chunks]

        # Verify structure
        assert isinstance(chunk_dicts, list)
        assert all(isinstance(d, dict) for d in chunk_dicts)
        assert all("content" in d for d in chunk_dicts)
        assert all("start" in d for d in chunk_dicts)
        assert all("end" in d for d in chunk_dicts)
        assert all("metadata" in d for d in chunk_dicts)
