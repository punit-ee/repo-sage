#!/usr/bin/env python
"""
Example: Using repo-sage with OpenRouter API for access to multiple LLM providers.

OpenRouter provides a unified API to access various LLM providers including:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude models)
- Meta (Llama models)
- Google (PaLM, Gemini)
- Mistral AI
- And many more!

Setup:
1. Get API key from: https://openrouter.ai/keys
2. Add to .env: OPENAI_API_KEY=sk-or-v1-your-key-here
3. Add to .env: OPENAI_BASE_URL=https://openrouter.ai/api/v1
4. Run: python example_openrouter.py
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_setup():
    """Check if OpenRouter is configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    print("🔍 Checking configuration...")
    print(f"   OPENAI_API_KEY: {'✅ SET' if api_key else '❌ NOT SET'}")
    if api_key:
        print(f"      Value: {api_key[:20]}... (hidden)")
    print(f"   OPENAI_BASE_URL: {base_url if base_url else '❌ NOT SET'}")
    print()

    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("\n📋 Setup steps:")
        print("   1. Get API key from: https://openrouter.ai/keys")
        print("   2. Add to .env: OPENAI_API_KEY=sk-or-v1-your-key-here")
        print("   3. Add to .env: OPENAI_BASE_URL=https://openrouter.ai/api/v1")
        return False

    if not base_url or base_url != "https://openrouter.ai/api/v1":
        if base_url:
            print(f"⚠️  OPENAI_BASE_URL is set to: {base_url}")
            print("   Expected for OpenRouter: https://openrouter.ai/api/v1")
        else:
            print("⚠️  OPENAI_BASE_URL not set")
        print("\n💡 To use OpenRouter, add to .env:")
        print("   OPENAI_BASE_URL=https://openrouter.ai/api/v1")
        print("\n   Or the examples will pass base_url explicitly in code.")
        print("   Either way works!")

    return True


def example_openrouter_basic():
    """Basic example using OpenRouter."""
    print("\n" + "=" * 80)
    print("Example 1: Basic OpenRouter Integration")
    print("=" * 80 + "\n")

    from repo_sage.llm_helpers import OpenAIHelper

    # Use OpenRouter with various models
    models = [
        "openai/gpt-4o-mini",  # OpenAI's GPT-4
        "anthropic/claude-3-haiku",  # Anthropic's Claude
        "meta-llama/llama-3-8b",  # Meta's Llama
    ]

    for model in models:
        print(f"\n🤖 Testing with {model}...")
        try:
            helper = OpenAIHelper(
                base_url="https://openrouter.ai/api/v1",
                model=model,
                temperature=0.1,
                max_tokens=100,
            )

            response = helper.generate(
                "Explain machine learning in one sentence.",
                system_message="You are a concise technical writer.",
            )

            print(f"✅ Response: {response}")

        except Exception as e:
            print(f"❌ Error: {e}")


def example_openrouter_chunking():
    """Example: Document chunking with OpenRouter."""
    print("\n" + "=" * 80)
    print("Example 2: Document Chunking with OpenRouter")
    print("=" * 80 + "\n")

    from repo_sage.chunking import DocumentChunker, IntelligentChunkingStrategy
    from repo_sage.llm_helpers import create_openai_chunking_function

    # Create LLM function for OpenRouter
    llm_func = create_openai_chunking_function(
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-4o-mini",  # or any other OpenRouter model
    )

    # Create strategy
    strategy = IntelligentChunkingStrategy(llm_function=llm_func)
    chunker = DocumentChunker(strategy)

    # Sample document
    document = {
        "content": """# Python Programming Guide

Python is a high-level programming language known for its simplicity.

## Data Types

Python has several built-in data types including strings, integers, floats, and lists.

## Functions

Functions in Python are defined using the def keyword and can accept parameters.

## Classes

Python supports object-oriented programming with classes and inheritance.""",
        "filename": "python_guide.md",
    }

    print("📝 Chunking document with OpenRouter...")
    try:
        chunks = chunker.chunk_documents([document])

        print(f"✅ Created {len(chunks)} chunks\n")
        for i, chunk in enumerate(chunks, 1):
            print(f"Chunk {i}:")
            print(f"  Length: {len(chunk.content)} chars")
            print(f"  Preview: {chunk.content[:80]}...")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")


def example_openrouter_models_comparison():
    """Compare different models available through OpenRouter."""
    print("\n" + "=" * 80)
    print("Example 3: Comparing Different LLM Providers")
    print("=" * 80 + "\n")

    from repo_sage.llm_helpers import OpenAIHelper

    # Different providers available through OpenRouter
    models = [
        ("OpenAI GPT-4 Mini", "openai/gpt-4o-mini"),
        ("Claude 3 Haiku", "anthropic/claude-3-haiku"),
        ("Llama 3 8B", "meta-llama/llama-3-8b-instruct"),
        ("Mistral 7B", "mistralai/mistral-7b-instruct"),
    ]

    prompt = "What is the capital of France? Answer in 5 words or less."

    for name, model_id in models:
        print(f"\n🤖 {name} ({model_id}):")
        try:
            helper = OpenAIHelper(
                base_url="https://openrouter.ai/api/v1",
                model=model_id,
                temperature=0.0,
                max_tokens=50,
            )

            response = helper.generate(prompt)
            print(f"   Response: {response}")

        except Exception as e:
            print(f"   ❌ Error: {e}")


def example_openrouter_with_fallback():
    """Example with fallback strategy."""
    print("\n" + "=" * 80)
    print("Example 4: OpenRouter with Fallback Strategy")
    print("=" * 80 + "\n")

    from repo_sage.chunking import (
        DocumentChunker,
        IntelligentChunkingStrategy,
        SlidingWindowStrategy,
    )
    from repo_sage.llm_helpers import create_openai_chunking_function

    # Create fallback
    fallback = SlidingWindowStrategy(window_size=500, step_size=250, min_chunk_size=100)

    # Create OpenRouter function
    llm_func = create_openai_chunking_function(
        base_url="https://openrouter.ai/api/v1", model="anthropic/claude-3-haiku"
    )

    # Create strategy with fallback
    strategy = IntelligentChunkingStrategy(
        llm_function=llm_func, max_retries=2, fallback_strategy=fallback
    )

    chunker = DocumentChunker(strategy)

    document = {
        "content": "x" * 1000,  # Simple test document
        "filename": "test.md",
    }

    print("📝 Chunking with fallback protection...")
    try:
        chunks = chunker.chunk_documents([document])
        method = chunks[0].metadata.get("chunk_method", "unknown")
        print(f"✅ Success! Method used: {method}")
        print(f"✅ Created {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_environment_based_config():
    """Example: Using environment variables for configuration."""
    print("\n" + "=" * 80)
    print("Example 5: Environment-Based Configuration")
    print("=" * 80 + "\n")

    from repo_sage.llm_helpers import create_openai_chunking_function

    # When OPENAI_BASE_URL is set in .env, no need to pass base_url
    print("📝 Using configuration from .env file...")
    print(f"   OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
    print(f"   API Key: {os.getenv('OPENAI_API_KEY', 'Not set')[:20]}...")

    try:
        # Reads OPENAI_BASE_URL and OPENAI_API_KEY from environment
        llm_func = create_openai_chunking_function(model="openai/gpt-4o-mini")

        test_response = llm_func("Say 'Hello from OpenRouter!'")
        print(f"\n✅ Response: {test_response}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples."""
    print(
        "\n╔════════════════════════════════════════════════════════════════════════╗"
    )
    print("║              OpenRouter Integration Examples                          ║")
    print("║                      repo-sage                                        ║")
    print("╚════════════════════════════════════════════════════════════════════════╝")

    # Check setup
    if not check_setup():
        print("\n⚠️  Please complete setup first!")
        return

    print("\n✅ OpenRouter configured correctly!\n")

    # Run examples
    try:
        example_environment_based_config()
        example_openrouter_basic()
        example_openrouter_chunking()
        example_openrouter_models_comparison()
        example_openrouter_with_fallback()

        print("\n" + "=" * 80)
        print("✅ All examples completed!")
        print("=" * 80)

        print("\n📚 Learn more:")
        print("   - OpenRouter: https://openrouter.ai")
        print("   - Available models: https://openrouter.ai/models")
        print("   - Pricing: https://openrouter.ai/docs#pricing")
        print()

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()
