"""Concrete chunking strategy implementations."""

import logging
from collections.abc import Callable
from typing import Any

from .chunker import Chunk, ChunkingError, ChunkingStrategy

logger = logging.getLogger(__name__)


class SlidingWindowStrategy(ChunkingStrategy):
    """
    Sliding window chunking strategy with overlapping windows.

    This strategy divides text into fixed-size chunks with a configurable
    step size, allowing for overlap between consecutive chunks.
    """

    def __init__(
        self,
        window_size: int = 2000,
        step_size: int = 1000,
        min_chunk_size: int = 100,
    ):
        """
        Initialize the SlidingWindowStrategy.

        Args:
            window_size: Size of each chunk in characters
            step_size: Number of characters to move the window forward
            min_chunk_size: Minimum size for the last chunk

        Raises:
            ValueError: If parameters are invalid
        """
        self.window_size = window_size
        self.step_size = step_size
        self.min_chunk_size = min_chunk_size
        self.validate_config()

    def validate_config(self) -> None:
        """
        Validate the strategy configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if self.step_size <= 0:
            raise ValueError("step_size must be positive")
        if self.min_chunk_size < 0:
            raise ValueError("min_chunk_size must be non-negative")
        if self.min_chunk_size > self.window_size:
            raise ValueError("min_chunk_size cannot exceed window_size")

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """
        Chunk text using sliding window approach.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of Chunk objects

        Raises:
            ChunkingError: If chunking fails
        """
        if not isinstance(text, str):
            raise ChunkingError("Text must be a string")

        chunks: list[Chunk] = []
        text_length = len(text)

        if text_length == 0:
            return chunks

        position = 0
        chunk_index = 0

        while position < text_length:
            end = min(position + self.window_size, text_length)
            chunk_content = text[position:end]

            # Skip if chunk is too small (except if it's the only chunk)
            if len(chunk_content) < self.min_chunk_size and position > 0:
                logger.debug(
                    f"Skipping small final chunk at position {position} "
                    f"(size: {len(chunk_content)})"
                )
                break

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update(
                {
                    "chunk_index": chunk_index,
                    "chunk_method": "sliding_window",
                    "window_size": self.window_size,
                    "step_size": self.step_size,
                    "overlap": max(0, self.window_size - self.step_size),
                }
            )

            chunk = Chunk(
                content=chunk_content,
                start=position,
                end=end,
                metadata=chunk_metadata,
            )
            chunks.append(chunk)

            chunk_index += 1
            position += self.step_size

        logger.debug(f"Created {len(chunks)} chunks using sliding window")
        return chunks


class IntelligentChunkingStrategy(ChunkingStrategy):
    """
    Intelligent chunking strategy using an LLM or custom function.

    This strategy uses a callable (like an LLM API call) to intelligently
    split documents into logical sections.
    """

    def __init__(
        self,
        llm_function: Callable[[str], str],
        prompt_template: str | None = None,
        max_retries: int = 3,
        fallback_strategy: ChunkingStrategy | None = None,
    ):
        """
        Initialize the IntelligentChunkingStrategy.

        Args:
            llm_function: Callable that takes a prompt and returns a response
            prompt_template: Template for the prompt (must contain {document})
            max_retries: Maximum number of retries on failure
            fallback_strategy: Strategy to use if LLM fails

        Raises:
            ValueError: If parameters are invalid
        """
        self.llm_function = llm_function
        self.prompt_template = prompt_template or self._default_prompt_template()
        self.max_retries = max_retries
        self.fallback_strategy = fallback_strategy
        self.validate_config()

    @staticmethod
    def _default_prompt_template() -> str:
        """Return the default prompt template."""
        return """
Split the provided document into logical sections
that make sense for a Q&A system.

Each section should be self-contained and cover
a specific topic or concept.

<DOCUMENT>
{document}
</DOCUMENT>

Use this format:

## Section Name

Section content with all relevant details

---

## Another Section Name

Another section content

---
""".strip()

    def validate_config(self) -> None:
        """
        Validate the strategy configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if not callable(self.llm_function):
            raise ValueError("llm_function must be callable")

        if "{document}" not in self.prompt_template:
            raise ValueError("prompt_template must contain {document} placeholder")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.fallback_strategy is not None and not isinstance(
            self.fallback_strategy, ChunkingStrategy
        ):
            raise ValueError("fallback_strategy must be a ChunkingStrategy instance")

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """
        Chunk text using LLM-based intelligent splitting.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of Chunk objects

        Raises:
            ChunkingError: If chunking fails and no fallback is available
        """
        if not isinstance(text, str):
            raise ChunkingError("Text must be a string")

        # Try LLM-based chunking with retries
        for attempt in range(self.max_retries):
            try:
                chunks = self._llm_chunk(text, metadata)
                if chunks:
                    return chunks
            except Exception as e:
                logger.warning(
                    f"LLM chunking attempt {attempt + 1} failed: {e}",
                    exc_info=True,
                )
                if attempt == self.max_retries - 1:
                    # Last attempt failed
                    break

        # Use fallback strategy if available
        if self.fallback_strategy:
            logger.info("Using fallback strategy for chunking")
            return self.fallback_strategy.chunk(text, metadata)

        raise ChunkingError(
            f"LLM chunking failed after {self.max_retries} attempts "
            "and no fallback strategy available"
        )

    def _llm_chunk(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Perform LLM-based chunking.

        Args:
            text: Text to chunk
            metadata: Optional metadata

        Returns:
            List of Chunk objects

        Raises:
            ChunkingError: If LLM call or parsing fails
        """
        try:
            # Create prompt
            prompt = self.prompt_template.format(document=text)

            # Call LLM
            response = self.llm_function(prompt)

            if not response or not isinstance(response, str):
                raise ChunkingError("Invalid LLM response")

            # Parse response into sections
            sections = [s.strip() for s in response.split("---") if s.strip()]

            if not sections:
                raise ChunkingError("No sections found in LLM response")

            # Create chunks from sections
            chunks = []
            position = 0

            for idx, section in enumerate(sections):
                # Try to find the section in the original text
                # This is approximate and may need refinement
                start = text.find(section[:50]) if len(section) >= 50 else position
                if start == -1:
                    start = position

                end = start + len(section)

                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update(
                    {
                        "chunk_index": idx,
                        "chunk_method": "intelligent_llm",
                        "section_count": len(sections),
                    }
                )

                chunk = Chunk(
                    content=section,
                    start=start,
                    end=end,
                    metadata=chunk_metadata,
                )
                chunks.append(chunk)
                position = end

            logger.debug(f"Created {len(chunks)} chunks using LLM")
            return chunks

        except Exception as e:
            raise ChunkingError(f"LLM chunking failed: {str(e)}") from e


class SemanticChunkingStrategy(ChunkingStrategy):
    """
    Semantic chunking strategy that splits on natural boundaries.

    This strategy respects paragraph breaks, sentence boundaries,
    and other natural divisions in the text.
    """

    def __init__(
        self,
        max_chunk_size: int = 2000,
        min_chunk_size: int = 100,
        respect_paragraphs: bool = True,
        respect_sentences: bool = True,
    ):
        """
        Initialize the SemanticChunkingStrategy.

        Args:
            max_chunk_size: Maximum chunk size in characters
            min_chunk_size: Minimum chunk size in characters
            respect_paragraphs: Whether to avoid breaking paragraphs
            respect_sentences: Whether to avoid breaking sentences
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.respect_paragraphs = respect_paragraphs
        self.respect_sentences = respect_sentences
        self.validate_config()

    def validate_config(self) -> None:
        """
        Validate the strategy configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be positive")
        if self.min_chunk_size < 0:
            raise ValueError("min_chunk_size must be non-negative")
        if self.min_chunk_size > self.max_chunk_size:
            raise ValueError("min_chunk_size cannot exceed max_chunk_size")

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """
        Chunk text using semantic boundaries.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of Chunk objects

        Raises:
            ChunkingError: If chunking fails
        """
        if not isinstance(text, str):
            raise ChunkingError("Text must be a string")

        if not text.strip():
            return []

        chunks = []

        if self.respect_paragraphs:
            # Split by paragraphs first
            paragraphs = text.split("\n\n")
        else:
            paragraphs = [text]

        current_chunk: list[str] = []
        current_size = 0
        position = 0
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_size = len(para)

            # If paragraph alone exceeds max size, split it
            if para_size > self.max_chunk_size:
                # Flush current chunk first
                if current_chunk:
                    chunk_content = "\n\n".join(current_chunk)
                    chunks.append(
                        self._create_chunk(
                            chunk_content, position, chunk_index, metadata
                        )
                    )
                    position += len(chunk_content)
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0

                # Split large paragraph
                if self.respect_sentences:
                    sub_chunks = self._split_by_sentences(para)
                else:
                    sub_chunks = [para]

                for sub_chunk in sub_chunks:
                    chunks.append(
                        self._create_chunk(sub_chunk, position, chunk_index, metadata)
                    )
                    position += len(sub_chunk)
                    chunk_index += 1

            # Add paragraph to current chunk if it fits
            elif current_size + para_size <= self.max_chunk_size:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for \n\n

            # Flush current chunk and start new one
            else:
                if current_chunk:
                    chunk_content = "\n\n".join(current_chunk)
                    chunks.append(
                        self._create_chunk(
                            chunk_content, position, chunk_index, metadata
                        )
                    )
                    position += len(chunk_content)
                    chunk_index += 1

                current_chunk = [para]
                current_size = para_size

        # Flush remaining chunk
        if current_chunk:
            chunk_content = "\n\n".join(current_chunk)
            if len(chunk_content) >= self.min_chunk_size:
                chunks.append(
                    self._create_chunk(chunk_content, position, chunk_index, metadata)
                )

        logger.debug(f"Created {len(chunks)} chunks using semantic boundaries")
        return chunks

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split text into sentences (simple implementation)."""
        import re

        # Simple sentence splitter
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size <= self.max_chunk_size:
                current.append(sentence)
                current_size += sentence_size + 1
            else:
                if current:
                    chunks.append(" ".join(current))
                current = [sentence]
                current_size = sentence_size

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _create_chunk(
        self,
        content: str,
        position: int,
        chunk_index: int,
        metadata: dict[str, Any] | None,
    ) -> Chunk:
        """Create a chunk with metadata."""
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata.update(
            {
                "chunk_index": chunk_index,
                "chunk_method": "semantic",
                "max_chunk_size": self.max_chunk_size,
            }
        )

        return Chunk(
            content=content,
            start=position,
            end=position + len(content),
            metadata=chunk_metadata,
        )
