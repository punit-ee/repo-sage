"""repo-sage: GitHub repository data extraction tool."""

from .github_reader import GitHubRepoReader, read_repo_data

__version__ = "0.1.0"
__all__ = ["read_repo_data", "GitHubRepoReader"]
