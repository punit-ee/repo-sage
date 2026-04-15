"""Tests for search module."""

import pytest

from repo_sage.search import SearchEngine, create_search_engine


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "content": "Python is a high-level programming language",
            "title": "Python Introduction",
            "id": 1,
        },
        {
            "content": "JavaScript is used for web development",
            "title": "JavaScript Basics",
            "id": 2,
        },
        {
            "content": "Machine learning with Python and TensorFlow",
            "title": "ML Guide",
            "id": 3,
        },
        {
            "content": "React is a JavaScript library for building user interfaces",
            "title": "React Tutorial",
            "id": 4,
        },
        {
            "content": "Data science using Python pandas and numpy",
            "title": "Data Science",
            "id": 5,
        },
    ]


class TestSearchEngineInitialization:
    """Test SearchEngine initialization."""

    def test_init_default_parameters(self):
        """Test initialization with default parameters."""
        engine = SearchEngine()
        assert engine.embedding_model_name == "all-MiniLM-L6-v2"
        assert engine.text_fields == ["content"]
        assert engine.keyword_fields == []
        assert engine._documents == []
        assert engine._embeddings == []

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters."""
        engine = SearchEngine(
            embedding_model="all-mpnet-base-v2",
            text_fields=["content", "title"],
            keyword_fields=["category"],
        )
        assert engine.embedding_model_name == "all-mpnet-base-v2"
        assert engine.text_fields == ["content", "title"]
        assert engine.keyword_fields == ["category"]

    def test_model_lazy_loading(self):
        """Test that model is loaded lazily."""
        engine = SearchEngine()
        assert engine._model is None
        # Access model property to trigger loading
        model = engine.model
        assert model is not None
        assert engine._model is not None


class TestSearchEngineFit:
    """Test SearchEngine fit method."""

    def test_fit_with_valid_documents(self, sample_documents):
        """Test fitting with valid documents."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        assert len(engine._documents) == len(sample_documents)
        assert len(engine._embeddings) == len(sample_documents)

    def test_fit_with_empty_documents(self):
        """Test fitting with empty documents raises error."""
        engine = SearchEngine()
        with pytest.raises(ValueError, match="Cannot fit on empty documents"):
            engine.fit([])

    def test_fit_with_invalid_documents(self):
        """Test fitting with invalid documents raises error."""
        engine = SearchEngine()
        with pytest.raises(ValueError, match="Documents must be a list"):
            engine.fit("not a list")  # type: ignore

    def test_fit_creates_embeddings(self, sample_documents):
        """Test that fit creates embeddings."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        assert len(engine._embeddings) > 0
        # Check embedding shape (should be a vector)
        assert hasattr(engine._embeddings[0], "shape")

    def test_fit_creates_text_index(self, sample_documents):
        """Test that fit creates text index."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        assert engine._text_index is not None


class TestVectorSearch:
    """Test vector search functionality."""

    def test_vector_search_basic(self, sample_documents):
        """Test basic vector search."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("python programming", search_type="vector", top_k=3)
        assert len(results) == 3
        assert all("_score" in doc for doc in results)
        assert all("_search_type" in doc for doc in results)
        assert all(doc["_search_type"] == "vector" for doc in results)

    def test_vector_search_relevance(self, sample_documents):
        """Test that vector search returns relevant results."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("python programming", search_type="vector", top_k=3)
        # First result should be about Python
        assert "python" in results[0]["content"].lower()

    def test_vector_search_top_k(self, sample_documents):
        """Test vector search respects top_k parameter."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("programming", search_type="vector", top_k=2)
        assert len(results) == 2

    def test_vector_search_scores_descending(self, sample_documents):
        """Test that results are sorted by score descending."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("python", search_type="vector", top_k=5)
        scores = [doc["_score"] for doc in results]
        assert scores == sorted(scores, reverse=True)


class TestTextSearch:
    """Test text search functionality."""

    def test_text_search_basic(self, sample_documents):
        """Test basic text search."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("python", search_type="text", top_k=3)
        assert len(results) <= 3
        assert all("_search_type" in doc for doc in results)

    def test_text_search_finds_exact_matches(self, sample_documents):
        """Test text search finds exact keyword matches."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("JavaScript", search_type="text", top_k=3)
        # Should find documents containing JavaScript
        assert len(results) > 0
        assert any("javascript" in doc["content"].lower() for doc in results)

    def test_text_search_top_k(self, sample_documents):
        """Test text search respects top_k parameter."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("python", search_type="text", top_k=1)
        assert len(results) <= 1


class TestHybridSearch:
    """Test hybrid search functionality."""

    def test_hybrid_search_basic(self, sample_documents):
        """Test basic hybrid search."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search(
            "python machine learning", search_type="hybrid", top_k=3
        )
        assert len(results) == 3
        assert all("_score" in doc for doc in results)
        assert all(doc["_search_type"] == "hybrid" for doc in results)

    def test_hybrid_search_combines_results(self, sample_documents):
        """Test that hybrid search combines vector and text results."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("python", search_type="hybrid", top_k=3)
        assert len(results) > 0
        # Should find Python-related documents
        assert any("python" in doc["content"].lower() for doc in results)

    def test_hybrid_search_vector_weight(self, sample_documents):
        """Test hybrid search with different vector weights."""
        engine = SearchEngine()
        engine.fit(sample_documents)

        # High vector weight
        results_vector = engine.search(
            "python", search_type="hybrid", top_k=3, vector_weight=0.9
        )

        # High text weight
        results_text = engine.search(
            "python", search_type="hybrid", top_k=3, vector_weight=0.1
        )

        # Both should return results
        assert len(results_vector) > 0
        assert len(results_text) > 0

    def test_hybrid_search_balanced_weight(self, sample_documents):
        """Test hybrid search with balanced weights."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search(
            "python programming", search_type="hybrid", top_k=3, vector_weight=0.5
        )
        assert len(results) == 3


class TestSearchValidation:
    """Test search parameter validation."""

    def test_search_without_fit_raises_error(self):
        """Test that searching without fitting raises error."""
        engine = SearchEngine()
        with pytest.raises(ValueError, match="Search engine not fitted"):
            engine.search("test query")

    def test_search_with_empty_query_raises_error(self, sample_documents):
        """Test that empty query raises error."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            engine.search("")

    def test_search_with_invalid_query_raises_error(self, sample_documents):
        """Test that invalid query type raises error."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            engine.search(None)  # type: ignore

    def test_search_with_invalid_top_k_raises_error(self, sample_documents):
        """Test that invalid top_k raises error."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        with pytest.raises(ValueError, match="top_k must be positive"):
            engine.search("test", top_k=0)

    def test_search_with_invalid_vector_weight_raises_error(self, sample_documents):
        """Test that invalid vector_weight raises error."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        with pytest.raises(ValueError, match="vector_weight must be between 0 and 1"):
            engine.search("test", search_type="hybrid", vector_weight=1.5)

    def test_search_with_invalid_search_type_raises_error(self, sample_documents):
        """Test that invalid search_type raises error."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        with pytest.raises(ValueError, match="Invalid search_type"):
            engine.search("test", search_type="invalid")  # type: ignore


class TestSearchEngineReset:
    """Test SearchEngine reset functionality."""

    def test_reset_clears_data(self, sample_documents):
        """Test that reset clears all data."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        assert len(engine._documents) > 0

        engine.reset()
        assert len(engine._documents) == 0
        assert len(engine._embeddings) == 0
        assert engine._text_index is None


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_search_engine(self, sample_documents):
        """Test create_search_engine convenience function."""
        engine = create_search_engine(sample_documents)
        assert len(engine._documents) == len(sample_documents)
        # Should be able to search immediately
        results = engine.search("python", search_type="vector", top_k=3)
        assert len(results) > 0

    def test_create_search_engine_with_custom_params(self, sample_documents):
        """Test create_search_engine with custom parameters."""
        engine = create_search_engine(
            sample_documents,
            text_fields=["content", "title"],
            keyword_fields=["id"],
        )
        assert engine.text_fields == ["content", "title"]
        assert engine.keyword_fields == ["id"]


class TestMultiFieldSearch:
    """Test search with multiple fields."""

    def test_search_multiple_text_fields(self):
        """Test search using multiple text fields."""
        documents = [
            {"content": "Python programming", "title": "Guide", "id": 1},
            {"content": "Web development", "title": "Python Tutorial", "id": 2},
        ]
        engine = SearchEngine(text_fields=["content", "title"])
        engine.fit(documents)
        results = engine.search("python", search_type="vector", top_k=2)
        # Both documents should match (one in content, one in title)
        assert len(results) == 2


class TestEdgeCases:
    """Test edge cases."""

    def test_search_with_single_document(self):
        """Test search with only one document."""
        documents = [{"content": "Python programming", "id": 1}]
        engine = SearchEngine()
        engine.fit(documents)
        results = engine.search("python", search_type="vector", top_k=5)
        assert len(results) == 1

    def test_search_with_top_k_larger_than_documents(self, sample_documents):
        """Test search with top_k larger than number of documents."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("python", search_type="vector", top_k=100)
        # Should return all documents
        assert len(results) == len(sample_documents)

    def test_search_with_special_characters(self, sample_documents):
        """Test search with special characters in query."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search(
            "python & machine-learning!", search_type="vector", top_k=3
        )
        assert len(results) > 0

    def test_search_with_unicode(self, sample_documents):
        """Test search with unicode characters."""
        engine = SearchEngine()
        engine.fit(sample_documents)
        results = engine.search("pythön programming 🐍", search_type="vector", top_k=3)
        assert len(results) > 0
