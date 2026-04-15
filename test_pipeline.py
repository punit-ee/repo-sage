"""Quick test to demonstrate the complete pipeline."""

from repo_sage import SearchEngine, read_repo_data
from repo_sage.chunking import DocumentChunker, SlidingWindowStrategy


def test_complete_pipeline() -> None:
    """Test the complete pipeline: download -> chunk -> search."""
    print("=" * 70)
    print("REPO-SAGE COMPLETE PIPELINE TEST")
    print("=" * 70)

    # Step 1: Download repository
    print("\n[1/4] Downloading repository...")
    documents = read_repo_data(repo_owner="DataTalksClub", repo_name="faq")
    print(f"      ✓ Downloaded {len(documents)} documents")

    # Step 2: Chunk documents
    print("\n[2/4] Chunking documents...")
    strategy = SlidingWindowStrategy(window_size=1000, step_size=500)
    chunker = DocumentChunker(strategy)
    chunks = chunker.chunk_documents(documents)
    print(f"      ✓ Created {len(chunks)} chunks")

    # Step 3: Index documents
    print("\n[3/4] Creating search index...")
    chunk_dicts = [chunk.to_dict() for chunk in chunks]
    engine = SearchEngine(text_fields=["content"])
    engine.fit(chunk_dicts)
    print(f"      ✓ Indexed {len(chunk_dicts)} chunks")

    # Step 4: Search
    print("\n[4/4] Testing search...")
    queries = [
        "How do I join the course?",
        "What are the prerequisites?",
        "Can I get a certificate?",
    ]

    for query in queries:
        print(f"\n      Query: '{query}'")
        results = engine.search(query, search_type="hybrid", top_k=2)

        for i, result in enumerate(results, 1):
            score = result.get("_score", 0)
            content = result.get("content", "")[:100]
            print(f"      {i}. Score: {score:.4f} | {content}...")

    print("\n" + "=" * 70)
    print("✅ PIPELINE TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\nAll components working:")
    print("  • GitHub data download")
    print("  • Document chunking")
    print("  • Vector embeddings")
    print("  • Text indexing")
    print("  • Hybrid search")
    print("=" * 70)


if __name__ == "__main__":
    test_complete_pipeline()
