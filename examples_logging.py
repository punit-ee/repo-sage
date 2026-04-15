"""Example demonstrating the agent logging system."""

from repo_sage import RepoAgent, SearchEngine
from repo_sage.log_analyzer import LogAnalyzer, view_logs
from repo_sage.logging_system import create_interaction_logger


def example_with_logging():
    """Example: Agent with interaction logging enabled."""
    print("=" * 70)
    print("AGENT WITH LOGGING SYSTEM")
    print("=" * 70)

    # Sample documents
    documents = [
        {
            "content": "To install, run: pip install my-project",
            "title": "Installation",
        },
        {
            "content": "Import with: from my_project import MyClass",
            "title": "Usage",
        },
        {
            "content": "Configure with config.yaml file in project root",
            "title": "Configuration",
        },
    ]

    print("\n[1/5] Creating search engine...")
    engine = SearchEngine()
    engine.fit(documents)
    print("      ✅ Search engine ready")

    print("\n[2/5] Creating agent with logging enabled...")
    agent = RepoAgent(
        search_engine=engine,
        model="openai:gpt-4o-mini",
        enable_logging=True,  # Enable logging
    )
    print("      ✅ Agent created with logging")

    print("\n[3/5] Asking questions (logged)...")

    questions = [
        "How do I install this project?",
        "How do I use this library?",
        "What configuration options are available?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n   Question {i}: {question}")
        try:
            answer = agent.ask(question)
            print(f"   Answer: {answer[:80]}...")
        except Exception as e:
            print(f"   Error: {e}")

    print("\n[4/5] Retrieving session statistics...")
    stats = agent.get_session_stats()
    print(f"      Session ID: {stats.get('session_id')}")
    print(f"      Interactions: {stats.get('interactions')}")
    print(f"      Log file: {stats.get('log_file')}")

    print("\n[5/5] Viewing conversation history...")
    history = agent.get_conversation_history(last_n=2)
    for i, interaction in enumerate(history, 1):
        print(f"\n      Interaction {i}:")
        print(f"      Q: {interaction['question']}")
        print(f"      A: {interaction['answer'][:60]}...")

    # Export conversation
    print("\n📁 Exporting conversation...")
    agent.export_conversation("logs/example_conversation.json")
    print("      ✅ Exported to logs/example_conversation.json")

    print("\n" + "=" * 70)
    print("✅ LOGGING DEMONSTRATION COMPLETE")
    print("=" * 70)

    return stats.get("log_file")


def example_log_analysis(log_file: str):
    """Example: Analyzing interaction logs."""
    print("\n" + "=" * 70)
    print("LOG ANALYSIS")
    print("=" * 70)

    print("\n[1/2] Loading and analyzing logs...")
    analyzer = LogAnalyzer(log_file)
    analyzer.print_report()

    print("\n[2/2] Viewing recent log entries...")
    view_logs(log_file, last_n=3)

    # Export report
    print("\n📊 Exporting analysis report...")
    analyzer.export_report("logs/analysis_report.json")

    print("\n" + "=" * 70)


def example_manual_logging():
    """Example: Using logging system directly."""
    print("\n" + "=" * 70)
    print("MANUAL LOGGING EXAMPLE")
    print("=" * 70)

    print("\n[1/3] Creating logger...")
    logger = create_interaction_logger(console_output=True)
    print("      ✅ Logger created")

    print("\n[2/3] Logging various events...")

    # Log interaction
    logger.log_interaction(
        question="What is the meaning of life?",
        answer="42",
        metadata={"response_time_seconds": 0.5, "model": "gpt-4"},
    )

    # Log search
    logger.log_search(
        query="python installation",
        search_type="hybrid",
        results_count=5,
        top_score=0.95,
        response_time=0.15,
    )

    # Log error
    logger.log_error(
        error_type="APIError",
        error_message="Rate limit exceeded",
        context={"endpoint": "/api/search", "retry_after": 60},
    )

    # Log performance
    logger.log_performance(
        operation="document_indexing",
        duration_seconds=2.5,
        metrics={"documents_processed": 100, "chunks_created": 250},
    )

    print("\n[3/3] Session statistics...")
    stats = logger.get_session_stats()
    print(f"      {stats}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("🔍 Agent Logging System Examples\n")

    # Example 1: Agent with logging
    try:
        log_file = example_with_logging()

        # Example 2: Analyze logs
        if log_file:
            example_log_analysis(log_file)

    except Exception as e:
        print(f"\n⚠️  Note: {e}")
        print("    Set OPENAI_API_KEY to run agent examples")

    # Example 3: Manual logging (always works)
    example_manual_logging()

    print("\n✅ All examples complete!")
    print("\n💡 Check the logs/ directory for output files")
