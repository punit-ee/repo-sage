# Search Module Documentation

## Overview

The `repo_sage.search` module provides a simple yet powerful search engine with three search strategies:

1. **Vector Search**: Semantic search using sentence transformers and cosine similarity
2. **Text Search**: Keyword-based search using BM25 algorithm (via minsearch)
3. **Hybrid Search**: Combines vector and text search using Reciprocal Rank Fusion (RRF)

## Features

- 🔍 **Three Search Types**: Vector, text, and hybrid search
- 🚀 **Simple API**: Single class with intuitive methods
- 📊 **Production Ready**: Full test coverage, type hints, logging
- 🎯 **Flexible**: Customize text fields, keyword fields, and search weights
- 🔄 **Hybrid Strategy**: Advanced RRF fusion of multiple search results
- ⚡ **Efficient**: Lazy loading of models, batch processing

## Installation

The search functionality requires additional dependencies:

```bash
# Already included in pyproject.toml
pip install sentence-transformers minsearch numpy

# Or with uv
uv pip install sentence-transformers minsearch numpy
```

## Quick Start

### Basic Usage

```python
from repo_sage.search import SearchEngine, create_search_engine

# Sample documents
documents = [
    {"content": "Python is a programming language", "id": 1},
    {"content": "JavaScript is used for web development", "id": 2},
    {"content": "Machine learning with Python", "id": 3},
]

# Create and fit search engine
engine = create_search_engine(documents)

# Vector search (semantic)
results = engine.search("python programming", search_type="vector", top_k=3)

# Text search (keyword-based)
results = engine.search("JavaScript", search_type="text", top_k=3)

# Hybrid search (best of both)
results = engine.search("machine learning", search_type="hybrid", top_k=3)
```

### With GitHub Data

```python
from repo_sage import read_repo_data, SearchEngine
from repo_sage.chunking import DocumentChunker, SlidingWindowStrategy

# Download repository
documents = read_repo_data("owner", "repo")

# Chunk documents
strategy = SlidingWindowStrategy(window_size=1000, step_size=500)
chunker = DocumentChunker(strategy)
chunks = chunker.chunk_documents(documents)

# Convert to dicts and search
chunk_dicts = [chunk.to_dict() for chunk in chunks]
engine = SearchEngine()
engine.fit(chunk_dicts)

# Search
results = engine.search("How do I install?", search_type="hybrid", top_k=5)
```

## API Reference

### SearchEngine

Main class for search functionality.

#### Constructor

```python
SearchEngine(
    embedding_model: str = "all-MiniLM-L6-v2",
    text_fields: list[str] | None = None,
    keyword_fields: list[str] | None = None,
)
```

**Parameters:**
- `embedding_model`: Sentence transformer model name (default: "all-MiniLM-L6-v2")
- `text_fields`: Fields to search in (default: ["content"])
- `keyword_fields`: Fields to use as keywords in text search (default: [])

**Recommended Models:**
- `all-MiniLM-L6-v2`: Fast, good quality (default)
- `all-mpnet-base-v2`: Higher quality, slower
- `multi-qa-MiniLM-L6-cos-v1`: Optimized for Q&A

#### Methods

##### fit()

Index documents for searching.

```python
engine.fit(documents: list[dict[str, Any]]) -> None
```

**Parameters:**
- `documents`: List of document dictionaries with text content

**Raises:**
- `ValueError`: If documents is empty or invalid

##### search()

Search documents using specified strategy.

```python
engine.search(
    query: str,
    search_type: Literal["vector", "text", "hybrid"] = "hybrid",
    top_k: int = 5,
    vector_weight: float = 0.5,
) -> list[dict[str, Any]]
```

**Parameters:**
- `query`: Search query string
- `search_type`: Type of search ("vector", "text", or "hybrid")
- `top_k`: Number of results to return
- `vector_weight`: Weight for vector search in hybrid mode (0.0-1.0)

**Returns:**
- List of documents with `_score` and `_search_type` fields

**Raises:**
- `ValueError`: If engine not fitted or invalid parameters

##### reset()

Clear all indexed data.

```python
engine.reset() -> None
```

### Convenience Functions

#### create_search_engine()

Create and fit a search engine in one step.

```python
create_search_engine(
    documents: list[dict[str, Any]],
    embedding_model: str = "all-MiniLM-L6-v2",
    text_fields: list[str] | None = None,
    keyword_fields: list[str] | None = None,
) -> SearchEngine
```

## Search Types Explained

### Vector Search

Uses semantic embeddings to find similar content by meaning, not exact words.

**Pros:**
- Understands semantic similarity
- Works with synonyms and paraphrases
- Good for questions and natural language queries

**Cons:**
- Slower than text search
- May miss exact keyword matches
- Requires more memory

**Best for:** Natural language queries, questions, semantic similarity

```python
results = engine.search("python programming", search_type="vector", top_k=5)
```

### Text Search

Traditional keyword-based search using BM25 algorithm.

**Pros:**
- Fast and lightweight
- Excellent for exact keyword matches
- No model loading required

**Cons:**
- Misses semantic similarity
- Doesn't understand synonyms
- Sensitive to exact wording

**Best for:** Keyword searches, exact matches, filtering

```python
results = engine.search("JavaScript", search_type="text", top_k=5)
```

### Hybrid Search

Combines vector and text search using Reciprocal Rank Fusion (RRF).

**Pros:**
- Best of both worlds
- Robust to different query types
- Balanced results

**Cons:**
- Slightly slower than individual methods
- More complex scoring

**Best for:** General purpose search, production systems

```python
results = engine.search(
    "machine learning tutorial",
    search_type="hybrid",
    top_k=5,
    vector_weight=0.5  # 50% vector, 50% text
)
```

### Tuning Hybrid Search

Adjust `vector_weight` based on your use case:

```python
# More semantic (better for questions)
results = engine.search(query, vector_weight=0.8)  # 80% vector, 20% text

# More keyword-based (better for exact matches)
results = engine.search(query, vector_weight=0.2)  # 20% vector, 80% text

# Balanced (default)
results = engine.search(query, vector_weight=0.5)  # 50% each
```

## Advanced Usage

### Multiple Text Fields

Search across multiple fields:

```python
engine = SearchEngine(
    text_fields=["title", "content", "description"],
    keyword_fields=["category", "tags"]
)
engine.fit(documents)
results = engine.search("query")
```

### Custom Embedding Models

Use different embedding models:

```python
# High quality model
engine = SearchEngine(embedding_model="all-mpnet-base-v2")

# Multilingual model
engine = SearchEngine(embedding_model="paraphrase-multilingual-MiniLM-L12-v2")

# Q&A optimized model
engine = SearchEngine(embedding_model="multi-qa-MiniLM-L6-cos-v1")
```

### Result Processing

Process search results:

```python
results = engine.search("query", top_k=10)

for result in results:
    score = result["_score"]
    search_type = result["_search_type"]
    content = result["content"]

    print(f"Score: {score:.3f} | Type: {search_type}")
    print(f"Content: {content[:100]}...")
```

## Performance Tips

### Model Selection

- **all-MiniLM-L6-v2**: Best balance of speed and quality (recommended)
- **all-mpnet-base-v2**: Higher quality, 2x slower
- **all-MiniLM-L12-v2**: Middle ground

### Batch Processing

Fit the engine once, search many times:

```python
# Expensive operation - do once
engine = SearchEngine()
engine.fit(large_document_list)

# Fast operations - do many times
results1 = engine.search("query1")
results2 = engine.search("query2")
results3 = engine.search("query3")
```

### Memory Management

For large document sets:

```python
# Use smaller embedding model
engine = SearchEngine(embedding_model="all-MiniLM-L6-v2")  # 384 dims

# Or reset after use
engine.fit(documents)
results = engine.search("query")
engine.reset()  # Free memory
```

## Testing

Run the test suite:

```bash
# Run search tests
pytest tests/test_search.py -v

# Run with coverage
pytest tests/test_search.py --cov=src/repo_sage/search

# Run all tests
pytest tests/
```

## Examples

See `examples_search.py` for complete examples:

```bash
python examples_search.py
```

## Troubleshooting

### Model Download Issues

Models are downloaded from HuggingFace Hub on first use:

```python
# Set HF_TOKEN for authenticated downloads (optional)
import os
os.environ["HF_TOKEN"] = "your_token_here"
```

### Memory Issues

If you encounter memory issues with large datasets:

1. Use a smaller embedding model
2. Chunk documents into smaller pieces
3. Process documents in batches
4. Use `engine.reset()` to free memory

### Slow Performance

To improve performance:

1. Use a faster embedding model (e.g., "all-MiniLM-L6-v2")
2. Reduce `top_k` parameter
3. Use text search instead of vector search when possible
4. Cache the fitted engine for reuse

## Design Patterns Used

- **Strategy Pattern**: Encapsulated in search type selection
- **Lazy Loading**: Model loaded only when needed
- **Factory Pattern**: `create_search_engine()` convenience function
- **Facade Pattern**: Simple interface hiding complex operations

## Best Practices

1. **Fit once, search many times**: Fitting is expensive, searching is fast
2. **Use hybrid search by default**: Best results for most use cases
3. **Tune vector_weight**: Adjust based on your query types
4. **Monitor memory usage**: Large document sets can use significant memory
5. **Add logging**: Use logging to debug search behavior

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Follow existing code style
3. Add type hints
4. Update documentation
5. Run pre-commit hooks

## License

See LICENSE file in the repository root.
