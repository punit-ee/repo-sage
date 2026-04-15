"""Example usage of RepoAgent with pydantic-ai."""

from repo_sage import SearchEngine, create_repo_agent


def example_basic_agent():
    """Example: Basic agent usage."""
    print("BASIC AGENT EXAMPLE")
    print("=" * 70)
    documents = [
        {"content": "Install with: pip install my-project", "title": "Installation"},
        {"content": "Import with: from my_project import MyClass", "title": "Usage"},
    ]
    engine = SearchEngine()
    engine.fit(documents)
    agent = create_repo_agent(engine, model="openai:gpt-4o-mini")
    question = "How do I install this project?"
    print(f"\nQuestion: {question}")
    answer = agent.ask(question)
    print(f"Answer: {answer}")


if __name__ == "__main__":
    print("Make sure OPENAI_API_KEY is set in your .env file!\n")
    example_basic_agent()
