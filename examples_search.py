"""Example usage of repo-sage search functionality."""

from repo_sage import SearchEngine, create_search_engine, read_repo_data
from repo_sage.chunking import DocumentChunker, SlidingWindowStrategy


def example_basic_search():
    """Example: Basic search on simple documents."""
    print("=== Basic Search Example ===\n")

    # Sample documents
    documents = [
        {
            "content": "Python is a high-level programming language known for its simplicity",
            "title": "Python Introduction",
            "id": 1,
        },
        {
            "content": "JavaScript is the language of the web, used for frontend and backend",
            "title": "JavaScript Basics",
            "id": 2,
        },
        {
            "content": "Machine learning with Python using scikit-learn and TensorFlow",
            "title": "ML with Python",
            "id": 3,
        },
        {
            "content": "React is a JavaScript library for building interactive user interfaces",
            "title": "React Guide",
            "id": 4,
        },
        {
            "content": "Data science and analysis with Python pandas and matplotlib",
            "title": "Data Science",
            "id": 5,
        },
    ]

    # Create and fit search engine
    engine = create_search_engine(documents)

    # Vector search
    print("Vector Search for 'python programming':")
    results = engine.search("python programming", search_type="vector", top_k=3)
    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc['title']} (score: {doc['_score']:.3f})")
        print(f"   {doc['content'][:60]}...\n")

    # Text search
    print("\nText Search for 'JavaScript':")
    results = engine.search("JavaScript", search_type="text", top_k=3)
    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc['title']}")
        print(f"   {doc['content'][:60]}...\n")

    # Hybrid search
    print("\nHybrid Search for 'machine learning':")
    results = engine.search("machine learning", search_type="hybrid", top_k=3)
    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc['title']} (score: {doc['_score']:.3f})")
        print(f"   {doc['content'][:60]}...\n")


def example_github_with_search():
    """Example: Download GitHub repo, chunk, and search."""
    print("\n=== GitHub Integration with Search ===\n")

    # Download repository
    print("Downloading repository...")
    documents = read_repo_data(
        repo_owner="DataTalksClub",
        repo_name="faq",
    )
    print(f"Downloaded {len(documents)} documents\n")

    # Chunk documents
    print("Chunking documents...")
    strategy = SlidingWindowStrategy(window_size=1000, step_size=500)
    chunker = DocumentChunker(strategy)
    chunks = chunker.chunk_documents(documents)
    print(f"Created {len(chunks)} chunks\n")

    # Convert chunks to dicts
    chunk_dicts = [chunk.to_dict() for chunk in chunks]

    # Create search engine
    print("Creating search engine...")
    engine = SearchEngine(text_fields=["content"])
    engine.fit(chunk_dicts)
    print("Search engine ready!\n")

    # Search examples
    queries = [
        "How do I join the course?",
        "What are the prerequisites?",
        "Can I get a certificate?",
    ]

    for query in queries:
        print(f"Query: '{query}'")
        print("-" * 60)

        # Hybrid search (best of both worlds)
        results = engine.search(query, search_type="hybrid", top_k=3)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['_score']:.3f}")
            content = result.get("content", "")
            print(f"   {content[:200]}...")
            if "metadata" in result and "filename" in result["metadata"]:
                print(f"   Source: {result['metadata']['filename']}")

        print("\n" + "=" * 60 + "\n")


def example_search_comparison():
    """Example: Compare different search types."""
    print("\n=== Search Type Comparison ===\n")

    documents = [
        {"content": "Python programming language tutorial", "id": 1},
        {"content": "Learn Python for data science", "id": 2},
        {"content": "JavaScript web development guide", "id": 3},
        {"content": "Python machine learning basics", "id": 4},
        {"content": "Advanced Python programming techniques", "id": 5},
    ]

    engine = create_search_engine(documents)
    query = "python programming"

    print(f"Query: '{query}'\n")

    # Compare search types
    for search_type in ["vector", "text", "hybrid"]:
        print(f"{search_type.upper()} Search Results:")
        results = engine.search(query, search_type=search_type, top_k=3)  # type: ignore
        for i, doc in enumerate(results, 1):
            score = doc.get("_score", 0)
            print(f"  {i}. (score: {score:.3f}) {doc['content']}")
        print()


def example_weighted_hybrid_search():
    """Example: Hybrid search with different weights."""
    print("\n=== Weighted Hybrid Search ===\n")

    documents = [
        {"content": "Python is great for machine learning", "id": 1},
        {"content": "JavaScript for web applications", "id": 2},
        {"content": "Data analysis with Python", "id": 3},
        {"content": "React and JavaScript frameworks", "id": 4},
    ]

    engine = create_search_engine(documents)
    query = "python data"

    print(f"Query: '{query}'\n")

    # Different weights
    weights = [
        (0.9, "Vector-heavy (0.9)"),
        (0.5, "Balanced (0.5)"),
        (0.1, "Text-heavy (0.1)"),
    ]

    for weight, label in weights:
        print(f"{label}:")
        results = engine.search(
            query, search_type="hybrid", top_k=2, vector_weight=weight
        )
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc['content']}")
        print()


def example_custom_fields():
    """Example: Search with custom fields."""
    print("\n=== Custom Fields Search ===\n")

    documents = [
        {
            "title": "Python Guide",
            "content": "Learn Python programming",
            "category": "tutorial",
            "id": 1,
        },
        {
            "title": "JavaScript Handbook",
            "content": "Master JavaScript development",
            "category": "tutorial",
            "id": 2,
        },
        {
            "title": "Python Reference",
            "content": "Complete Python API reference",
            "category": "reference",
            "id": 3,
        },
    ]

    # Search across multiple fields
    engine = SearchEngine(text_fields=["title", "content"], keyword_fields=["category"])
    engine.fit(documents)

    query = "Python"
    print(f"Searching for '{query}' across title and content:\n")

    results = engine.search(query, search_type="vector", top_k=3)
    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc['title']}")
        print(f"   Category: {doc['category']}")
        print(f"   Score: {doc['_score']:.3f}\n")


def example_interactive_search():
    """Example: Interactive search demo."""
    print("\n=== Interactive Search Demo ===\n")

    # Sample knowledge base
    documents = [
        {
            "content": "Python is an interpreted, high-level programming language with dynamic typing",
            "title": "Python Basics",
            "id": 1,
        },
        {
            "content": "NumPy is the fundamental package for scientific computing with Python",
            "title": "NumPy",
            "id": 2,
        },
        {
            "content": "Pandas provides high-performance data structures and analysis tools",
            "title": "Pandas",
            "id": 3,
        },
        {
            "content": "Scikit-learn is a machine learning library for Python",
            "title": "Scikit-learn",
            "id": 4,
        },
        {
            "content": "TensorFlow is an end-to-end platform for machine learning",
            "title": "TensorFlow",
            "id": 5,
        },
        {
            "content": "Matplotlib is a comprehensive library for creating visualizations in Python",
            "title": "Matplotlib",
            "id": 6,
        },
    ]

    engine = create_search_engine(documents)

    print("Knowledge base loaded with", len(documents), "documents\n")
    print("Try these queries:")
    print("  - 'machine learning'")
    print("  - 'data visualization'")
    print("  - 'scientific computing'")
    print()

    # Example queries
    example_queries = [
        "machine learning",
        "data visualization",
        "scientific computing",
    ]

    for query in example_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 50)
        results = engine.search(query, search_type="hybrid", top_k=2)
        for i, doc in enumerate(results, 1):
            print(f"{i}. {doc['title']} (score: {doc['_score']:.3f})")
            print(f"   {doc['content']}")


if __name__ == "__main__":
    # Run examples
    # example_basic_search()
    example_github_with_search()  # Uncomment to test with real GitHub data
    # example_search_comparison()
    # example_weighted_hybrid_search()
    # example_custom_fields()
    # example_interactive_search()
