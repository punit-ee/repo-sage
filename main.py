"""Complete end-to-end integration example for repo-sage."""

import logging
import os

from repo_sage import SearchEngine, create_repo_agent, read_repo_data
from repo_sage.chunking import DocumentChunker, SlidingWindowStrategy
from repo_sage.exceptions import InvalidRepositoryError, RepositoryDownloadError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """
    Complete end-to-end integration demonstration.

    This demonstrates the full pipeline:
    1. Download GitHub repository
    2. Chunk documents
    3. Index for search
    4. Perform searches
    5. Use AI agent for Q&A
    """
    print("=" * 70)
    print("🚀 repo-sage: Complete End-to-End Integration")
    print("=" * 70)

    # Step 1: Download Repository
    print("\n[1/5] 📥 Downloading GitHub repository...")
    print("      Repository: DataTalksClub/faq")

    try:
        documents = read_repo_data("DataTalksClub", "faq", "main")
        print(f"      ✅ Successfully extracted {len(documents)} markdown files")

        # Show sample files
        print("\n      📄 Sample files:")
        for item in documents[:3]:
            filename = item.get("filename", "Unknown")
            print(f"         • {filename}")
        if len(documents) > 3:
            print(f"         ... and {len(documents) - 3} more files")

    except (InvalidRepositoryError, RepositoryDownloadError) as e:
        print(f"\n      ❌ Error: {e}")
        print("      Falling back to demo data...")
        # Fallback demo data
        documents = [
            {
                "content": "# Installation\n\nTo install, run: pip install my-project",
                "filename": "install.md",
            },
            {
                "content": "# Getting Started\n\nImport with: from my_project import MyClass",
                "filename": "quickstart.md",
            },
        ]
        print(f"      ℹ️  Using {len(documents)} demo documents")

    # Step 2: Chunk Documents
    print("\n[2/5] ✂️  Chunking documents...")
    print("      Strategy: Sliding Window (size=1000, step=500)")

    strategy = SlidingWindowStrategy(window_size=1000, step_size=500)
    chunker = DocumentChunker(strategy)
    chunks = chunker.chunk_documents(documents)
    chunk_dicts = [chunk.to_dict() for chunk in chunks]

    print(f"      ✅ Created {len(chunk_dicts)} chunks")

    # Step 3: Index for Search
    print("\n[3/5] 🔍 Creating search index...")
    print("      Indexing with vector and text search...")

    engine = SearchEngine(text_fields=["content"])
    engine.fit(chunk_dicts)

    print(f"      ✅ Indexed {len(chunk_dicts)} chunks")

    # Step 4: Perform Searches
    print("\n[4/5] 🔎 Testing search functionality...")

    test_queries = [
        ("How do I join the course?", "hybrid"),
        ("installation", "text"),
        ("getting started", "vector"),
    ]

    for query, search_type in test_queries:
        print(f"\n      Query: '{query}' ({search_type} search)")
        results = engine.search(query, search_type=search_type, top_k=2)  # type: ignore

        for i, result in enumerate(results[:2], 1):
            score = result.get("_score", 0)
            content = result.get("content", "")[:80]
            print(f"      {i}. Score: {score:.4f} | {content}...")

    # Step 5: AI Agent Q&A (if API key available)
    print("\n[5/5] 🤖 AI Agent Q&A System...")

    if os.getenv("OPENAI_API_KEY"):
        print("      Creating AI agent with search tools...")

        try:
            agent = create_repo_agent(engine, model="openai:gpt-4o-mini")
            print("      ✅ Agent created successfully")

            # Ask a question
            question = "How can I join the course?"
            print(f"\n      Question: {question}")
            print("      Agent is searching and formulating answer...")

            answer = agent.ask(question)
            print(f"\n      Answer:\n      {answer[:200]}...")

        except Exception as e:
            print(f"      ⚠️  Agent error: {e}")
            print("      Continuing with search-only mode...")
    else:
        print("      ⚠️  OPENAI_API_KEY not set - skipping AI agent demo")
        print("      💡 Set OPENAI_API_KEY in .env to enable AI agent")

    # Summary
    print("\n" + "=" * 70)
    print("✅ COMPLETE PIPELINE EXECUTED SUCCESSFULLY")
    print("=" * 70)

    print("\n📊 Summary:")
    print(f"   • Documents downloaded: {len(documents)}")
    print(f"   • Chunks created: {len(chunk_dicts)}")
    print("   • Search engine: Ready")
    print(
        f"   • AI Agent: {'Ready' if os.getenv('OPENAI_API_KEY') else 'Disabled (no API key)'}"
    )

    print("\n💡 Next Steps:")
    print("   • Run: python examples_search.py")
    print("   • Run: python examples_agent.py")
    print("   • Run: python setup_check.py")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
