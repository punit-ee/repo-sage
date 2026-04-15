"""Simple search module with vector, text, and hybrid search capabilities."""

import logging
from typing import Any, Literal

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from minsearch import Index
except ImportError:
    Index = None

logger = logging.getLogger(__name__)

SearchType = Literal["vector", "text", "hybrid"]


class SearchEngine:
    """
    Simple search engine supporting vector, text, and hybrid search.

    This class provides a unified interface for searching through documents
    using different search strategies.

    Example:
        >>> engine = SearchEngine()
        >>> documents = [
        ...     {"content": "Python is great", "id": 1},
        ...     {"content": "JavaScript is awesome", "id": 2}
        ... ]
        >>> engine.fit(documents)
        >>> results = engine.search("python programming", search_type="vector", top_k=5)
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        text_fields: list[str] | None = None,
        keyword_fields: list[str] | None = None,
    ):
        """
        Initialize the SearchEngine.

        Args:
            embedding_model: Name of sentence-transformer model for embeddings
            text_fields: Fields to use for text search (default: ["content"])
            keyword_fields: Fields to use as keywords in text search (default: [])
        """
        self.embedding_model_name = embedding_model
        self.text_fields = text_fields or ["content"]
        self.keyword_fields = keyword_fields or []

        # Lazy initialization
        self._model: SentenceTransformer | None = None
        self._text_index: Any = None
        self._documents: list[dict[str, Any]] = []
        self._embeddings: np.ndarray | list[Any] = []

        logger.info(f"Initialized SearchEngine with model: {embedding_model}")

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self._model = SentenceTransformer(self.embedding_model_name)
        assert self._model is not None  # For type checker
        return self._model

    def fit(self, documents: list[dict[str, Any]]) -> None:
        """
        Index documents for searching.

        Args:
            documents: List of document dictionaries

        Raises:
            ValueError: If documents is empty or invalid
        """
        if not documents:
            raise ValueError("Cannot fit on empty documents list")

        if not isinstance(documents, list):
            raise ValueError("Documents must be a list")

        logger.info(f"Fitting search engine on {len(documents)} documents")

        # Store documents
        self._documents = documents

        # Create embeddings for vector search
        self._create_embeddings(documents)

        # Create text index for text search
        self._create_text_index(documents)

        logger.info("Search engine fitted successfully")

    def _create_embeddings(self, documents: list[dict[str, Any]]) -> None:
        """Create embeddings for all documents."""
        texts = [self._get_text_for_embedding(doc) for doc in documents]
        logger.info("Creating embeddings for documents...")
        self._embeddings = self.model.encode(texts, show_progress_bar=False)
        logger.info(f"Created {len(self._embeddings)} embeddings")

    def _get_text_for_embedding(self, doc: dict[str, Any]) -> str:
        """Extract text from document for embedding."""
        # Combine all text fields
        parts = []
        for field in self.text_fields:
            if field in doc and doc[field]:
                parts.append(str(doc[field]))
        return " ".join(parts) if parts else ""

    def _create_text_index(self, documents: list[dict[str, Any]]) -> None:
        """Create text search index."""
        if Index is None:
            logger.warning("minsearch not available, text search disabled")
            return

        logger.info("Creating text search index...")
        self._text_index = Index(
            text_fields=self.text_fields, keyword_fields=self.keyword_fields
        )
        self._text_index.fit(documents)
        logger.info("Text index created successfully")

    def search(
        self,
        query: str,
        search_type: SearchType = "hybrid",
        top_k: int = 5,
        vector_weight: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Search documents using specified search type.

        Args:
            query: Search query string
            search_type: Type of search - "vector", "text", or "hybrid"
            top_k: Number of results to return
            vector_weight: Weight for vector search in hybrid mode (0.0-1.0)
                          Text search gets (1 - vector_weight)

        Returns:
            List of documents sorted by relevance

        Raises:
            ValueError: If engine is not fitted or parameters are invalid
        """
        if not self._documents:
            raise ValueError("Search engine not fitted. Call fit() first.")

        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        if not 0 <= vector_weight <= 1:
            raise ValueError("vector_weight must be between 0 and 1")

        logger.info(
            f"Searching with type={search_type}, query='{query[:50]}...', top_k={top_k}"
        )

        if search_type == "vector":
            return self._vector_search(query, top_k)
        elif search_type == "text":
            return self._text_search(query, top_k)
        elif search_type == "hybrid":
            return self._hybrid_search(query, top_k, vector_weight)
        else:
            raise ValueError(f"Invalid search_type: {search_type}")

    def _vector_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """
        Perform vector similarity search.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of documents with similarity scores
        """
        # Encode query
        query_embedding = self.model.encode(query, show_progress_bar=False)

        # Calculate similarities
        similarities = np.dot(self._embeddings, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Return documents with scores
        results = []
        for idx in top_indices:
            doc = self._documents[idx].copy()
            doc["_score"] = float(similarities[idx])
            doc["_search_type"] = "vector"
            results.append(doc)

        logger.info(f"Vector search returned {len(results)} results")
        return results

    def _text_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """
        Perform text-based search using minsearch.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of documents with relevance scores
        """
        if self._text_index is None:
            logger.warning("Text index not available, returning empty results")
            return []

        # Perform text search
        results: list[dict[str, Any]] = self._text_index.search(
            query, num_results=top_k
        )

        # Add metadata
        for doc in results:
            doc["_search_type"] = "text"
            # minsearch returns documents with scores, just ensure key exists
            if "_score" not in doc:
                doc["_score"] = 1.0

        logger.info(f"Text search returned {len(results)} results")
        return results

    def _hybrid_search(
        self,
        query: str,
        top_k: int,
        vector_weight: float,
    ) -> list[dict[str, Any]]:
        """
        Perform hybrid search combining vector and text search.

        Uses Reciprocal Rank Fusion (RRF) to combine rankings.

        Args:
            query: Search query
            top_k: Number of results
            vector_weight: Weight for vector search (0.0-1.0)

        Returns:
            List of documents with combined scores
        """
        # Get more results to improve fusion quality
        fusion_k = min(top_k * 3, len(self._documents))

        # Get results from both searches
        vector_results = self._vector_search(query, fusion_k)
        text_results = self._text_search(query, fusion_k)

        # Combine using weighted RRF
        combined_scores: dict[int, float] = {}

        # Process vector results
        for rank, doc in enumerate(vector_results, 1):
            doc_id = id(doc)  # Use object id as unique identifier
            # Store document reference
            if doc_id not in combined_scores:
                combined_scores[doc_id] = 0.0
            # RRF score: 1 / (k + rank), with weight
            combined_scores[doc_id] += vector_weight * (1.0 / (60 + rank))

        # Process text results
        text_weight = 1.0 - vector_weight
        for rank, doc in enumerate(text_results, 1):
            doc_id = id(doc)
            if doc_id not in combined_scores:
                combined_scores[doc_id] = 0.0
            combined_scores[doc_id] += text_weight * (1.0 / (60 + rank))

        # Create document lookup
        doc_lookup = {}
        for doc in vector_results + text_results:
            doc_lookup[id(doc)] = doc

        # Sort by combined score
        sorted_ids = sorted(
            combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True
        )

        # Return top-k results
        results = []
        for doc_id in sorted_ids[:top_k]:
            doc = doc_lookup[doc_id].copy()
            doc["_score"] = combined_scores[doc_id]
            doc["_search_type"] = "hybrid"
            results.append(doc)

        logger.info(f"Hybrid search returned {len(results)} results")
        return results

    def reset(self) -> None:
        """Reset the search engine, clearing all indexed data."""
        self._documents = []
        self._embeddings = []
        self._text_index = None
        logger.info("Search engine reset")


def create_search_engine(
    documents: list[dict[str, Any]],
    embedding_model: str = "all-MiniLM-L6-v2",
    text_fields: list[str] | None = None,
    keyword_fields: list[str] | None = None,
) -> SearchEngine:
    """
    Convenience function to create and fit a search engine in one step.

    Args:
        documents: List of documents to index
        embedding_model: Name of sentence-transformer model
        text_fields: Fields to use for text search
        keyword_fields: Fields to use as keywords

    Returns:
        Fitted SearchEngine instance

    Example:
        >>> documents = [{"content": "Python programming", "id": 1}]
        >>> engine = create_search_engine(documents)
        >>> results = engine.search("python", search_type="vector")
    """
    engine = SearchEngine(
        embedding_model=embedding_model,
        text_fields=text_fields,
        keyword_fields=keyword_fields,
    )
    engine.fit(documents)
    return engine
