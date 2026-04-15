"""Example usage of evaluation system."""

from repo_sage.evaluation import AIJudge, PerformanceMetrics, TestDataGenerator


def example_simple_evaluation():
    """Example: Simple evaluation with AI judge."""
    print("=" * 70)
    print("SIMPLE EVALUATION EXAMPLE")
    print("=" * 70)

    # Sample test case
    question = "How do I install Python?"
    agent_answer = "You can install Python by downloading it from python.org and running the installer."
    ground_truth = "Download Python from python.org and run the installer for your operating system."

    print(f"\nQuestion: {question}")
    print(f"Answer: {agent_answer}")

    # Create judge
    judge = AIJudge(model="openai:gpt-4o-mini")

    # Evaluate
    print("\n🧪 Evaluating with AI judge...")
    evaluation = judge.evaluate_sync(question, agent_answer, ground_truth)

    print("\n📊 Evaluation Results:")
    if "overall_score" in evaluation:
        print(f"   Overall Score: {evaluation['overall_score']}/10")
    if "scores" in evaluation:
        print("   Detailed Scores:")
        for category, score in evaluation["scores"].items():
            print(f"      {category}: {score}/10")
    if "feedback" in evaluation:
        print(f"\n   Feedback: {evaluation['feedback'][:150]}...")

    print("\n" + "=" * 70)


def example_generate_test_data():
    """Example: Generate test questions automatically."""
    print("\n" + "=" * 70)
    print("TEST DATA GENERATION EXAMPLE")
    print("=" * 70)

    context = """
# Python Installation Guide

Python is a programming language. To install:

1. Go to python.org
2. Download the installer for your OS
3. Run the installer
4. Verify with: python --version

# Configuration

After installation, you may need to configure your PATH.
    """

    print("\n📝 Generating test questions from context...")

    generator = TestDataGenerator(model="openai:gpt-4o-mini")

    try:
        test_cases = generator.generate_sync(context, num_questions=5)

        print(f"\n✅ Generated {len(test_cases)} test cases:\n")

        for i, test in enumerate(test_cases, 1):
            print(f"{i}. Q: {test['question']}")
            print(f"   A: {test.get('ground_truth', 'N/A')[:80]}...")
            print(f"   Difficulty: {test.get('difficulty', 'N/A')}")
            print()

        # Save test set
        generator.save_test_set(test_cases, "test_data/generated_tests.json")
        print("💾 Saved to: test_data/generated_tests.json")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Note: Make sure OPENAI_API_KEY is set")

    print("\n" + "=" * 70)


def example_performance_metrics():
    """Example: Track performance metrics."""
    print("\n" + "=" * 70)
    print("PERFORMANCE METRICS EXAMPLE")
    print("=" * 70)

    # Create metrics tracker
    metrics = PerformanceMetrics()

    # Simulate some evaluations
    print("\n📊 Adding sample evaluations...")

    sample_evaluations = [
        {"overall_score": 9.5, "scores": {"accuracy": 10, "clarity": 9}},
        {"overall_score": 7.5, "scores": {"accuracy": 8, "clarity": 7}},
        {"overall_score": 8.0, "scores": {"accuracy": 8, "clarity": 8}},
        {"overall_score": 6.5, "scores": {"accuracy": 7, "clarity": 6}},
        {"overall_score": 9.0, "scores": {"accuracy": 9, "clarity": 9}},
    ]

    for eval_result in sample_evaluations:
        metrics.add_evaluation(eval_result)

    # Print summary
    metrics.print_summary()

    # Export
    metrics.export_metrics("metrics/sample_metrics.json")
    print("\n💾 Exported to: metrics/sample_metrics.json")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("🧪 Evaluation System Examples\n")

    # Example 1: Simple evaluation
    try:
        example_simple_evaluation()
    except Exception as e:
        print(f"⚠️  {e}")

    # Example 2: Generate test data
    try:
        example_generate_test_data()
    except Exception as e:
        print(f"⚠️  {e}")

    # Example 3: Metrics (always works)
    example_performance_metrics()

    print("\n✅ Examples complete!")
