"""Integration tests for GitHub repository reader."""

import pytest

from repo_sage import GitHubRepoReader, read_repo_data
from repo_sage.exceptions import RepositoryDownloadError


@pytest.mark.integration
class TestGitHubRepoReaderIntegration:
    """
    Integration tests that make real requests to GitHub.

    These tests are marked with @pytest.mark.integration and can be skipped
    with: pytest -m "not integration"
    """

    def test_read_public_repository(self):
        """Test reading from a real public repository."""
        # Using a small, stable test repository
        # Note: This makes a real network request
        try:
            data = read_repo_data("github", "gitignore", "main")
            assert isinstance(data, list)
            # The gitignore repo should have at least a README
            assert len(data) >= 1
        except RepositoryDownloadError:
            pytest.skip("Network request failed - may be offline or rate limited")

    def test_read_nonexistent_repository(self):
        """Test reading from a non-existent repository."""
        with pytest.raises(RepositoryDownloadError, match="Repository not found"):
            read_repo_data("nonexistent-user-12345", "nonexistent-repo-67890", "main")

    def test_read_invalid_branch(self):
        """Test reading from an invalid branch."""
        with pytest.raises(RepositoryDownloadError):
            read_repo_data("github", "gitignore", "nonexistent-branch-xyz")

    def test_context_manager_usage(self):
        """Test using GitHubRepoReader as context manager with real request."""
        try:
            with GitHubRepoReader() as reader:
                data = reader.read_repo_data("github", "gitignore", "main")
                assert isinstance(data, list)
        except RepositoryDownloadError:
            pytest.skip("Network request failed")
