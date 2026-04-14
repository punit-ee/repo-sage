"""Example usage of repo-sage with chunking strategies."""

from repo_sage.chunking import (
    DocumentChunker,
    IntelligentChunkingStrategy,
    SemanticChunkingStrategy,
    SlidingWindowStrategy,
)


def example_sliding_window():
    """Example: Simple sliding window chunking."""
    print("=== Sliding Window Chunking Example ===\n")

    # Create strategy with 2000 char windows, 1000 char steps
    strategy = SlidingWindowStrategy(
        window_size=2000, step_size=1000, min_chunk_size=100
    )

    # Create chunker
    chunker = DocumentChunker(strategy)

    # Simulate documents (or use read_repo_data from GitHub)
    documents = [
        {
            "content": "Lorem ipsum " * 200,  # Long content
            "filename": "doc1.md",
            "title": "Document 1",
        }
    ]

    # Chunk documents
    chunks = chunker.chunk_documents(documents)

    print(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"\nChunk {i}:")
        print(f"  Start: {chunk.start}, End: {chunk.end}")
        print(f"  Length: {len(chunk.content)}")
        print(f"  Overlap: {chunk.metadata.get('overlap', 0)}")
        print(f"  Preview: {chunk.content[:50]}...")


def example_semantic_chunking():
    """Example: Semantic chunking with paragraph boundaries."""
    print("\n=== Semantic Chunking Example ===\n")

    # Create strategy that respects paragraphs and sentences
    strategy = SemanticChunkingStrategy(
        max_chunk_size=2000,
        min_chunk_size=100,
        respect_paragraphs=True,
        respect_sentences=True,
    )

    chunker = DocumentChunker(strategy)

    # Markdown document with clear structure
    documents = [
        {
            "content": """# Introduction

This is the introduction paragraph.

## Section 1: Getting Started

Here we explain how to get started with the project.

## Section 2: Advanced Features

This section covers advanced features and use cases.

## Conclusion

Final thoughts and next steps.""",
            "filename": "readme.md",
        }
    ]

    chunks = chunker.chunk_documents(documents)

    print(f"Created {len(chunks)} semantic chunks")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Method: {chunk.metadata['chunk_method']}")
        print(f"  Content preview:\n{chunk.content[:100]}...")


def example_intelligent_chunking():
    """Example: Intelligent chunking with LLM."""
    print("\n=== Intelligent Chunking Example ===\n")

    # Mock LLM function (in production, use OpenAI or similar)
    def mock_llm(prompt: str) -> str:
        """Simulate LLM response."""
        # In production, this would call an actual LLM API
        # For example:
        # response = openai_client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # return response.choices[0].message.content

        return """## Introduction and Setup

Getting started with the project and initial setup instructions.

---

## Core Concepts

Explanation of the main concepts and architecture.

---

## API Reference

Detailed API documentation and examples."""

    # Create strategy with fallback
    fallback = SlidingWindowStrategy(window_size=2000, step_size=1000)
    strategy = IntelligentChunkingStrategy(
        llm_function=mock_llm, max_retries=3, fallback_strategy=fallback
    )

    chunker = DocumentChunker(strategy)

    documents = [
        {
            "content": "Long technical document content...",
            "filename": "docs.md",
        }
    ]

    chunks = chunker.chunk_documents(documents)

    print(f"Created {len(chunks)} intelligent chunks")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Method: {chunk.metadata['chunk_method']}")
        print(f"  Section: {chunk.metadata.get('section_count', 'N/A')}")
        print(f"  Content:\n{chunk.content[:150]}...")


def example_github_integration():
    """Example: Full pipeline from GitHub to chunks."""
    print("\n=== GitHub Integration Example ===\n")

    # Note: This requires a valid GitHub repository
    # Uncomment and modify for actual use:
    #
    # # Download repository
    # documents = read_repo_data(
    #     repo_owner="octocat",
    #     repo_name="Hello-World",
    #     branch_name="main"
    # )
    #
    # print(f"Downloaded {len(documents)} documents from GitHub")
    #
    # # Chunk the documents
    # strategy = SlidingWindowStrategy(window_size=2000, step_size=1000)
    # chunker = DocumentChunker(strategy)
    # chunks = chunker.chunk_documents(documents)
    #
    # print(f"Created {len(chunks)} chunks")
    #
    # # Export to dict for storage
    # chunk_dicts = [chunk.to_dict() for chunk in chunks]
    # print(f"Exported {len(chunk_dicts)} chunk dictionaries")

    print("(This example requires a valid GitHub repository)")


def example_strategy_comparison():
    """Example: Compare different strategies on same data."""
    print("\n=== Strategy Comparison Example ===\n")

    document = {
        "content": """# Technical Documentation

This is a comprehensive guide to using our system.

## Installation

Follow these steps to install the software.

## Configuration

Configure the system according to your needs.

## Usage

Learn how to use the main features.

## Troubleshooting

Common issues and their solutions.""",
        "filename": "guide.md",
    }

    strategies = [
        ("Sliding Window", SlidingWindowStrategy(window_size=100, step_size=50)),
        (
            "Semantic",
            SemanticChunkingStrategy(max_chunk_size=100, min_chunk_size=20),
        ),
    ]

    for name, strategy in strategies:
        chunker = DocumentChunker(strategy)
        chunks = chunker.chunk_documents([document])
        print(f"{name}: {len(chunks)} chunks")


def example_custom_openai_integration():
    """Example: Using with actual OpenAI API."""
    print("\n=== OpenAI Integration Example ===\n")

    try:
        from repo_sage.chunking import (
            IntelligentChunkingStrategy,
            SlidingWindowStrategy,
        )
        from repo_sage.llm_helpers import create_openai_chunking_function

        # Create OpenAI function (uses OPENAI_API_KEY from .env)
        llm_func = create_openai_chunking_function(
            model="gpt-4o-mini"  # or "gpt-4" for better quality
        )

        # Create fallback strategy
        fallback = SlidingWindowStrategy(
            window_size=2000, step_size=1000, min_chunk_size=100
        )

        # Create intelligent strategy with OpenAI
        strategy = IntelligentChunkingStrategy(
            llm_function=llm_func, max_retries=3, fallback_strategy=fallback
        )

        # Example document
        documents = [
            {
                "content": """# Machine Learning Guide

Machine learning is a subset of artificial intelligence.

## Supervised Learning

Supervised learning uses labeled data to train models.
Common algorithms include regression and classification.

## Unsupervised Learning

Unsupervised learning finds patterns in unlabeled data.
Clustering and dimensionality reduction are key techniques.

## Deep Learning

Deep learning uses neural networks with multiple layers.
It has revolutionized computer vision and NLP.""",
                "filename": "ml_guide.md",
            }
        ]

        # Chunk with OpenAI
        chunker = DocumentChunker(strategy)
        chunks = chunker.chunk_documents(documents)

        print(f"✅ Successfully created {len(chunks)} chunks using OpenAI")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"  Method: {chunk.metadata['chunk_method']}")
            preview = chunk.content[:80].replace("\n", " ")
            print(f"  Content: {preview}...")

    except ImportError:
        print("⚠️  OpenAI not installed. Install with: pip install openai")
        print("   Or: uv add openai")
    except ValueError as e:
        print(f"⚠️  {e}")
        print("   Set your API key in .env file:")
        print("   OPENAI_API_KEY=your_key_here")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run all examples
    example_sliding_window()
    example_semantic_chunking()
    example_intelligent_chunking()
    example_github_integration()
    example_strategy_comparison()
    example_custom_openai_integration()
