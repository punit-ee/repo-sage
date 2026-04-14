"""repo-sage: GitHub repository data extraction tool."""

from . import chunking
from .github_reader import GitHubRepoReader, read_repo_data

# Optional LLM helpers (requires openai package)
try:
    from . import llm_helpers
except ImportError:
    llm_helpers = None  # noqa: F811

__version__ = "0.1.0"
__all__ = ["read_repo_data", "GitHubRepoReader", "chunking", "llm_helpers"]
