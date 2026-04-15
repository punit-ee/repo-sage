"""Complete example: Java Design Patterns repository analysis."""

import time

from repo_sage import (
    AIJudge,
    PerformanceMetrics,
    RepoAgent,
    SearchEngine,
    TestDataGenerator,
    read_repo_data,
)
from repo_sage.chunking import DocumentChunker, SlidingWindowStrategy


def main():
    """Complete pipeline for Java Design Patterns repository."""
    print("=" * 70)
    print("🎯 JAVA DESIGN PATTERNS REPOSITORY ANALYSIS")
    print("Repository: https://github.com/iluwatar/java-design-patterns")
    print("=" * 70)

    # Step 1: Download Repository
    print("\n[1/6] 📥 Downloading repository...")
    print("      This may take a moment...")
    start_time = time.time()

    try:
        documents = read_repo_data(
            repo_owner="iluwatar",
            repo_name="java-design-patterns",
            branch_name="master",
        )
        download_time = time.time() - start_time
        print(f"      ✅ Downloaded {len(documents)} markdown files")
        print(f"      ⏱️  Time: {download_time:.2f}s")

        # Show sample files
        print("\n      📄 Sample files:")
        for doc in documents[:5]:
            filename = doc.get("filename", "Unknown").split("/")[-1]
            print(f"         • {filename}")
        if len(documents) > 5:
            print(f"         ... and {len(documents) - 5} more files")

    except Exception as e:
        print(f"      ❌ Error downloading: {e}")
        return

    # Step 2: Chunk Documents
    print("\n[2/6] ✂️  Chunking documents...")
    start_time = time.time()

    strategy = SlidingWindowStrategy(
        window_size=1500, step_size=750, min_chunk_size=100
    )
    chunker = DocumentChunker(strategy)
    chunks = chunker.chunk_documents(documents)
    chunk_dicts = [chunk.to_dict() for chunk in chunks]

    chunk_time = time.time() - start_time
    print(f"      ✅ Created {len(chunk_dicts)} chunks")
    print(f"      ⏱️  Time: {chunk_time:.2f}s")

    # Step 3: Create Search Index
    print("\n[3/6] 🔍 Creating search index...")
    print("      Building embeddings and text index...")
    start_time = time.time()

    engine = SearchEngine(text_fields=["content"])
    engine.fit(chunk_dicts)

    index_time = time.time() - start_time
    print(f"      ✅ Indexed {len(chunk_dicts)} chunks")
    print(f"      ⏱️  Time: {index_time:.2f}s")

    # Step 4: Test Search Functionality
    print("\n[4/6] 🔎 Testing search on design patterns...")

    search_queries = [
        ("What is the Singleton pattern?", "hybrid"),
        ("Factory pattern", "text"),
        ("design patterns for concurrency", "vector"),
    ]

    for query, search_type in search_queries:
        print(f"\n      Query: '{query}' ({search_type})")
        results = engine.search(query, search_type=search_type, top_k=3)  # type: ignore

        for i, result in enumerate(results[:2], 1):
            score = result.get("_score", 0)
            content = result.get("content", "")[:100].replace("\n", " ")
            print(f"      {i}. [{score:.3f}] {content}...")

    # Step 5: Create AI Agent
    print("\n[5/6] 🤖 Creating AI agent with search tools...")

    try:
        agent = RepoAgent(
            search_engine=engine, model="openai:gpt-4o-mini", enable_logging=True
        )
        print("      ✅ Agent created successfully")

        # Ask questions about design patterns
        print("\n      💬 Asking questions about design patterns...")

        questions = [
            "What is the Singleton pattern and when should I use it?",
            "Explain the Factory pattern with a simple example",
            "What are the main differences between Adapter and Decorator patterns?",
        ]

        answers = []
        for i, question in enumerate(questions, 1):
            print(f"\n      Q{i}: {question}")
            try:
                answer = agent.ask(question)
                answers.append({"question": question, "answer": answer})
                print(f"      A{i}: {answer[:150]}...")
            except Exception as e:
                print(f"      ❌ Error: {e}")
                print("      Make sure OPENAI_API_KEY is set in .env")

        # Show session stats
        if answers:
            stats = agent.get_session_stats()
            print("\n      📊 Session Stats:")
            print(f"         Interactions: {stats.get('interactions', 0)}")
            print(f"         Log file: {stats.get('log_file', 'N/A')}")

    except Exception as e:
        print(f"      ⚠️  Agent creation failed: {e}")
        print("      Skipping agent Q&A (requires OPENAI_API_KEY)")
        answers = []

    # Step 6: Automated Evaluation (if agent worked)
    if answers:
        print("\n[6/6] 📊 Running automated evaluation...")

        try:
            # Generate test questions from first document
            print("      🧪 Generating test questions...")
            generator = TestDataGenerator(model="openai:gpt-4o-mini")

            # Use first few documents as context
            context_docs = documents[:3]
            context = "\n\n".join(
                [doc.get("content", "")[:2000] for doc in context_docs]
            )

            test_cases = generator.generate_sync(context, num_questions=5)
            print(f"      ✅ Generated {len(test_cases)} test cases")

            # Show generated tests
            print("\n      📝 Sample test questions:")
            for i, test in enumerate(test_cases[:3], 1):
                print(f"      {i}. {test.get('question', 'N/A')[:70]}...")
                print(
                    f"         Difficulty: {test.get('difficulty', 'N/A')}, Category: {test.get('category', 'N/A')}"
                )

            # Evaluate agent on generated tests
            print("\n      🎯 Evaluating agent performance...")
            judge = AIJudge(model="openai:gpt-4o-mini")
            metrics = PerformanceMetrics()

            for i, test in enumerate(test_cases, 1):
                print(f"      [{i}/{len(test_cases)}] Evaluating...")

                answer = agent.ask(test["question"])
                evaluation = judge.evaluate_sync(
                    question=test["question"],
                    answer=answer,
                    ground_truth=test.get("ground_truth"),
                )

                metrics.add_evaluation(evaluation)

                if "overall_score" in evaluation:
                    score = evaluation["overall_score"]
                    print(f"         Score: {score:.1f}/10")

            # Print evaluation summary
            print("\n      📈 Evaluation Results:")
            metrics_data = metrics.get_metrics()
            print(
                f"         Average Score: {metrics_data.get('average_overall_score', 0):.1f}/10"
            )
            print(
                f"         Total Evaluations: {metrics_data.get('total_evaluations', 0)}"
            )

            # Export results
            metrics.export_metrics(
                "evaluation_results/java_design_patterns_metrics.json"
            )
            print("      💾 Results exported to: evaluation_results/")

        except Exception as e:
            print(f"      ⚠️  Evaluation error: {e}")
            print("      Note: Evaluation requires OPENAI_API_KEY")

    else:
        print("\n[6/6] ⚠️  Skipping evaluation (agent not available)")

    # Summary
    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)

    print("\n📊 Summary:")
    print("   • Repository: iluwatar/java-design-patterns")
    print(f"   • Documents downloaded: {len(documents)}")
    print(f"   • Chunks created: {len(chunk_dicts)}")
    print("   • Search engine: Ready")
    print(f"   • AI Agent: {'Ready' if answers else 'Not available (no API key)'}")

    print("\n💡 What you can do now:")
    print("   • Search design patterns:")
    print('     results = engine.search("observer pattern", search_type="hybrid")')
    print("\n   • Ask questions:")
    print('     answer = agent.ask("When should I use the Strategy pattern?")')
    print("\n   • Analyze logs:")
    print("     from repo_sage import LogAnalyzer")
    print('     analyzer = LogAnalyzer("logs/agent_interactions.jsonl")')
    print("     analyzer.print_report()")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("🚀 Starting Java Design Patterns Repository Analysis\n")
    print("This demonstrates the complete repo-sage pipeline:")
    print("  1. Download from GitHub")
    print("  2. Chunk documents")
    print("  3. Create search index")
    print("  4. AI agent Q&A")
    print("  5. Generate test cases")
    print("  6. Automated evaluation\n")

    main()

    print("\n✨ Analysis complete! Check the logs/ and evaluation_results/ directories")
