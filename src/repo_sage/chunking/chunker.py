"""Core chunking functionality with Strategy pattern implementation."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from ..exceptions import ChunkingError

logger = logging.getLogger(__name__)


class Chunk:
    """Represents a single chunk of content with metadata."""

    def __init__(
        self,
        content: str,
        start: int,
        end: int,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize a Chunk.

        Args:
            content: The chunk content
            start: Starting position in the original document
            end: Ending position in the original document
            metadata: Additional metadata for the chunk
        """
        if not isinstance(content, str):
            raise ValueError("Chunk content must be a string")
        if start < 0 or end < start:
            raise ValueError("Invalid chunk boundaries")

        self.content = content
        self.start = start
        self.end = end
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """
        Convert chunk to dictionary.

        Returns:
            Dictionary representation of the chunk
        """
        return {
            "content": self.content,
            "start": self.start,
            "end": self.end,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Chunk(start={self.start}, end={self.end}, length={len(self.content)})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Chunk."""
        if not isinstance(other, Chunk):
            return NotImplemented
        return (
            self.content == other.content
            and self.start == other.start
            and self.end == other.end
            and self.metadata == other.metadata
        )


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""

    @abstractmethod
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """
        Chunk the provided text.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of Chunk objects

        Raises:
            ChunkingError: If chunking fails
        """
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate the strategy configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass


class DocumentChunker:
    """
    Context class that uses a ChunkingStrategy to chunk documents.

    This class implements the Strategy pattern, allowing different
    chunking algorithms to be used interchangeably.
    """

    def __init__(self, strategy: ChunkingStrategy):
        """
        Initialize the DocumentChunker.

        Args:
            strategy: The chunking strategy to use

        Raises:
            TypeError: If strategy is not a ChunkingStrategy instance
        """
        if not isinstance(strategy, ChunkingStrategy):
            raise TypeError("strategy must be an instance of ChunkingStrategy")

        self.strategy = strategy
        self.strategy.validate_config()

    def set_strategy(self, strategy: ChunkingStrategy) -> None:
        """
        Change the chunking strategy.

        Args:
            strategy: New chunking strategy to use

        Raises:
            TypeError: If strategy is not a ChunkingStrategy instance
        """
        if not isinstance(strategy, ChunkingStrategy):
            raise TypeError("strategy must be an instance of ChunkingStrategy")

        self.strategy = strategy
        self.strategy.validate_config()

    def chunk_document(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Chunk a single document.

        Args:
            text: Document text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of Chunk objects

        Raises:
            ChunkingError: If chunking fails
        """
        if not isinstance(text, str):
            raise ChunkingError("Document text must be a string")

        if not text.strip():
            logger.warning("Empty document provided for chunking")
            return []

        try:
            chunks = self.strategy.chunk(text, metadata)
            logger.info(f"Successfully created {len(chunks)} chunks")
            return chunks
        except Exception as e:
            raise ChunkingError(f"Failed to chunk document: {str(e)}") from e

    def chunk_documents(
        self,
        documents: list[dict[str, Any]],
        content_field: str = "content",
    ) -> list[Chunk]:
        """
        Chunk multiple documents.

        Args:
            documents: List of document dictionaries
            content_field: Field name containing the text content

        Returns:
            List of all chunks from all documents

        Raises:
            ChunkingError: If chunking fails
        """
        if not isinstance(documents, list):
            raise ChunkingError("documents must be a list")

        all_chunks = []

        for idx, doc in enumerate(documents):
            if not isinstance(doc, dict):
                logger.warning(f"Skipping non-dict document at index {idx}")
                continue

            content = doc.get(content_field)
            if not content or not isinstance(content, str):
                logger.warning(
                    f"Skipping document at index {idx}: "
                    f"missing or invalid '{content_field}' field"
                )
                continue

            # Create metadata from document, excluding content
            metadata = {k: v for k, v in doc.items() if k != content_field}
            metadata["document_index"] = idx

            try:
                chunks = self.chunk_document(content, metadata)
                all_chunks.extend(chunks)
            except ChunkingError as e:
                logger.error(f"Error chunking document at index {idx}: {e}")
                continue

        logger.info(
            f"Processed {len(documents)} documents, created {len(all_chunks)} total chunks"
        )
        return all_chunks
