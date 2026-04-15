"""repo-sage: GitHub repository data extraction tool."""

from . import chunking
from .github_reader import GitHubRepoReader, read_repo_data
from .search import SearchEngine, create_search_engine

# Optional LLM helpers (requires openai package)
try:
    from . import llm_helpers
except ImportError:
    llm_helpers = None

# Optional agent (requires pydantic-ai package)
try:
    from .agent import RepoAgent, create_repo_agent
except ImportError:
    RepoAgent = None  # type: ignore
    create_repo_agent = None

# Logging system
try:
    from .log_analyzer import LogAnalyzer, view_logs
    from .logging_system import (
        AgentInteractionLogger,
        ConversationTracker,
        create_interaction_logger,
    )
except ImportError:
    LogAnalyzer = None  # type: ignore
    view_logs = None
    AgentInteractionLogger = None  # type: ignore
    ConversationTracker = None  # type: ignore
    create_interaction_logger = None

# Evaluation system
try:
    from .evaluation import (
        AIJudge,
        PerformanceMetrics,
        TestDataGenerator,
        create_ai_judge,
        create_test_generator,
    )
except ImportError:
    AIJudge = None  # type: ignore
    PerformanceMetrics = None  # type: ignore
    TestDataGenerator = None  # type: ignore
    create_ai_judge = None
    create_test_generator = None

__version__ = "0.1.0"
__all__ = [
    "read_repo_data",
    "GitHubRepoReader",
    "chunking",
    "llm_helpers",
    "SearchEngine",
    "create_search_engine",
    "RepoAgent",
    "create_repo_agent",
    "AgentInteractionLogger",
    "ConversationTracker",
    "create_interaction_logger",
    "LogAnalyzer",
    "view_logs",
    "AIJudge",
    "PerformanceMetrics",
    "TestDataGenerator",
    "create_ai_judge",
    "create_test_generator",
]
