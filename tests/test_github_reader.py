"""Unit tests for GitHub repository reader."""

import io
import zipfile
from unittest.mock import Mock, patch

import pytest
import requests

from repo_sage.exceptions import (
    InvalidRepositoryError,
    RepositoryDownloadError,
)
from repo_sage.github_reader import (
    DEFAULT_BRANCH,
    GITHUB_CODELOAD_PREFIX,
    GitHubRepoReader,
    read_repo_data,
)


class TestGitHubRepoReader:
    """Test cases for GitHubRepoReader class."""

    def test_initialization(self):
        """Test GitHubRepoReader initialization."""
        reader = GitHubRepoReader(timeout=60, max_file_size=5000000)
        assert reader.timeout == 60
        assert reader.max_file_size == 5000000
        assert reader.session is not None

    def test_context_manager(self):
        """Test GitHubRepoReader as context manager."""
        with GitHubRepoReader() as reader:
            assert reader.session is not None
        # Session should be closed after exiting context

    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs."""
        reader = GitHubRepoReader()
        # Should not raise any exception
        reader._validate_inputs("octocat", "Hello-World", "main")

    def test_validate_inputs_empty_owner(self):
        """Test input validation with empty owner."""
        reader = GitHubRepoReader()
        with pytest.raises(
            InvalidRepositoryError, match="repo_owner must be a non-empty string"
        ):
            reader._validate_inputs("", "repo", "main")

    def test_validate_inputs_empty_name(self):
        """Test input validation with empty repository name."""
        reader = GitHubRepoReader()
        with pytest.raises(
            InvalidRepositoryError, match="repo_name must be a non-empty string"
        ):
            reader._validate_inputs("owner", "", "main")

    def test_validate_inputs_empty_branch(self):
        """Test input validation with empty branch name."""
        reader = GitHubRepoReader()
        with pytest.raises(
            InvalidRepositoryError, match="branch_name must be a non-empty string"
        ):
            reader._validate_inputs("owner", "repo", "")

    def test_validate_inputs_invalid_type(self):
        """Test input validation with invalid types."""
        reader = GitHubRepoReader()
        with pytest.raises(InvalidRepositoryError):
            reader._validate_inputs(123, "repo", "main")

    def test_validate_inputs_invalid_characters(self):
        """Test input validation with invalid characters."""
        reader = GitHubRepoReader()
        with pytest.raises(InvalidRepositoryError, match="invalid characters"):
            reader._validate_inputs("owner<>", "repo", "main")

    def test_build_download_url(self):
        """Test URL building."""
        reader = GitHubRepoReader()
        url = reader._build_download_url("octocat", "Hello-World", "main")
        expected = f"{GITHUB_CODELOAD_PREFIX}/octocat/Hello-World/zip/refs/heads/main"
        assert url == expected

    def test_build_download_url_custom_branch(self):
        """Test URL building with custom branch."""
        reader = GitHubRepoReader()
        url = reader._build_download_url("user", "repo", "develop")
        expected = f"{GITHUB_CODELOAD_PREFIX}/user/repo/zip/refs/heads/develop"
        assert url == expected

    def test_is_markdown_file_md(self):
        """Test markdown file detection for .md extension."""
        reader = GitHubRepoReader()
        assert reader._is_markdown_file("README.md") is True
        assert reader._is_markdown_file("docs/guide.MD") is True

    def test_is_markdown_file_mdx(self):
        """Test markdown file detection for .mdx extension."""
        reader = GitHubRepoReader()
        assert reader._is_markdown_file("component.mdx") is True
        assert reader._is_markdown_file("page.MDX") is True

    def test_is_markdown_file_non_markdown(self):
        """Test markdown file detection for non-markdown files."""
        reader = GitHubRepoReader()
        assert reader._is_markdown_file("script.py") is False
        assert reader._is_markdown_file("data.json") is False
        assert reader._is_markdown_file("image.png") is False

    @patch("repo_sage.github_reader.requests.Session.get")
    def test_download_repository_success(self, mock_get):
        """Test successful repository download."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake zip content"
        mock_get.return_value = mock_response

        reader = GitHubRepoReader()
        content = reader._download_repository("http://example.com/repo.zip")

        assert content == b"fake zip content"
        mock_get.assert_called_once()

    @patch("repo_sage.github_reader.requests.Session.get")
    def test_download_repository_404(self, mock_get):
        """Test repository download with 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        reader = GitHubRepoReader()
        with pytest.raises(RepositoryDownloadError, match="Repository not found"):
            reader._download_repository("http://example.com/repo.zip")

    @patch("repo_sage.github_reader.requests.Session.get")
    def test_download_repository_403(self, mock_get):
        """Test repository download with 403 error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        reader = GitHubRepoReader()
        with pytest.raises(RepositoryDownloadError, match="Access forbidden"):
            reader._download_repository("http://example.com/repo.zip")

    @patch("repo_sage.github_reader.requests.Session.get")
    def test_download_repository_500(self, mock_get):
        """Test repository download with 500 error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        reader = GitHubRepoReader()
        with pytest.raises(RepositoryDownloadError, match="Failed to download"):
            reader._download_repository("http://example.com/repo.zip")

    @patch("repo_sage.github_reader.requests.Session.get")
    def test_download_repository_timeout(self, mock_get):
        """Test repository download with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()

        reader = GitHubRepoReader()
        with pytest.raises(RepositoryDownloadError, match="Download timeout"):
            reader._download_repository("http://example.com/repo.zip")

    @patch("repo_sage.github_reader.requests.Session.get")
    def test_download_repository_connection_error(self, mock_get):
        """Test repository download with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        reader = GitHubRepoReader()
        with pytest.raises(RepositoryDownloadError, match="Connection error"):
            reader._download_repository("http://example.com/repo.zip")

    def test_parse_markdown_file_success(self):
        """Test successful markdown file parsing."""
        reader = GitHubRepoReader()
        content = b"""---
title: Test Document
author: John Doe
---
# Hello World
This is a test."""

        result = reader._parse_markdown_file(content, "test.md")

        assert result is not None
        assert result["filename"] == "test.md"
        assert result["title"] == "Test Document"
        assert result["author"] == "John Doe"
        assert "Hello World" in result["content"]

    def test_parse_markdown_file_no_frontmatter(self):
        """Test markdown file parsing without frontmatter."""
        reader = GitHubRepoReader()
        content = b"# Hello World\nThis is a test."

        result = reader._parse_markdown_file(content, "test.md")

        assert result is not None
        assert result["filename"] == "test.md"
        assert "Hello World" in result["content"]

    def test_parse_markdown_file_invalid_utf8(self):
        """Test markdown file parsing with invalid UTF-8."""
        reader = GitHubRepoReader()
        content = b"# Hello \xff\xfe World"

        result = reader._parse_markdown_file(content, "test.md")

        assert result is not None
        assert result["filename"] == "test.md"

    def create_test_zip(self, files):
        """Helper method to create a test zip file."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)
        return zip_buffer.getvalue()

    def test_extract_markdown_files_success(self):
        """Test successful extraction of markdown files."""
        files = {
            "repo-main/README.md": b"""---
title: README
---
# Project""",
            "repo-main/docs/guide.md": b"""---
title: Guide
---
# Guide""",
            "repo-main/script.py": b"print('hello')",
        }
        zip_content = self.create_test_zip(files)

        reader = GitHubRepoReader()
        result = reader._extract_markdown_files(zip_content)

        assert len(result) == 2
        filenames = [r["filename"] for r in result]
        assert "repo-main/README.md" in filenames
        assert "repo-main/docs/guide.md" in filenames

    def test_extract_markdown_files_mdx(self):
        """Test extraction of .mdx files."""
        files = {
            "repo-main/page.mdx": b"""---
title: Page
---
# Page Content""",
        }
        zip_content = self.create_test_zip(files)

        reader = GitHubRepoReader()
        result = reader._extract_markdown_files(zip_content)

        assert len(result) == 1
        assert result[0]["filename"] == "repo-main/page.mdx"

    def test_extract_markdown_files_empty_zip(self):
        """Test extraction from empty zip."""
        zip_content = self.create_test_zip({})

        reader = GitHubRepoReader()
        result = reader._extract_markdown_files(zip_content)

        assert len(result) == 0

    def test_extract_markdown_files_no_markdown(self):
        """Test extraction from zip with no markdown files."""
        files = {
            "repo-main/script.py": b"print('hello')",
            "repo-main/data.json": b"{}",
        }
        zip_content = self.create_test_zip(files)

        reader = GitHubRepoReader()
        result = reader._extract_markdown_files(zip_content)

        assert len(result) == 0

    def test_extract_markdown_files_large_file_skipped(self):
        """Test that large files are skipped."""
        # Create a file larger than max_file_size
        large_content = b"#" * (11 * 1024 * 1024)  # 11MB
        files = {
            "repo-main/large.md": large_content,
            "repo-main/small.md": b"# Small",
        }
        zip_content = self.create_test_zip(files)

        reader = GitHubRepoReader(max_file_size=10 * 1024 * 1024)  # 10MB
        result = reader._extract_markdown_files(zip_content)

        # Only small file should be extracted
        assert len(result) == 1
        assert result[0]["filename"] == "repo-main/small.md"

    def test_extract_markdown_files_invalid_zip(self):
        """Test extraction with invalid zip content."""
        reader = GitHubRepoReader()
        with pytest.raises(RepositoryDownloadError, match="Invalid zip file"):
            reader._extract_markdown_files(b"not a zip file")

    @patch.object(GitHubRepoReader, "_download_repository")
    @patch.object(GitHubRepoReader, "_extract_markdown_files")
    def test_read_repo_data_integration(self, mock_extract, mock_download):
        """Test read_repo_data integration."""
        mock_download.return_value = b"fake zip content"
        mock_extract.return_value = [
            {"filename": "README.md", "title": "README", "content": "# Test"}
        ]

        reader = GitHubRepoReader()
        result = reader.read_repo_data("octocat", "Hello-World", "main")

        assert len(result) == 1
        assert result[0]["filename"] == "README.md"
        mock_download.assert_called_once()
        mock_extract.assert_called_once()

    @patch.object(GitHubRepoReader, "_download_repository")
    @patch.object(GitHubRepoReader, "_extract_markdown_files")
    def test_read_repo_data_default_branch(self, mock_extract, mock_download):
        """Test read_repo_data with default branch."""
        mock_download.return_value = b"fake zip content"
        mock_extract.return_value = []

        reader = GitHubRepoReader()
        reader.read_repo_data("octocat", "Hello-World")

        # Should use default branch
        call_args = mock_download.call_args[0][0]
        assert "refs/heads/main" in call_args

    def test_read_repo_data_invalid_inputs(self):
        """Test read_repo_data with invalid inputs."""
        reader = GitHubRepoReader()

        with pytest.raises(InvalidRepositoryError):
            reader.read_repo_data("", "repo", "main")

        with pytest.raises(InvalidRepositoryError):
            reader.read_repo_data("owner", "", "main")

        with pytest.raises(InvalidRepositoryError):
            reader.read_repo_data("owner", "repo", "")


class TestConvenienceFunction:
    """Test cases for the convenience function."""

    @patch.object(GitHubRepoReader, "read_repo_data")
    def test_read_repo_data_function(self, mock_method):
        """Test the convenience function."""
        mock_method.return_value = [{"filename": "test.md"}]

        result = read_repo_data("owner", "repo", "main")

        assert len(result) == 1
        assert result[0]["filename"] == "test.md"
        mock_method.assert_called_once_with("owner", "repo", "main")

    @patch.object(GitHubRepoReader, "read_repo_data")
    def test_read_repo_data_function_default_branch(self, mock_method):
        """Test the convenience function with default branch."""
        mock_method.return_value = []

        read_repo_data("owner", "repo")

        mock_method.assert_called_once_with("owner", "repo", DEFAULT_BRANCH)


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_parse_markdown_file_with_malformed_frontmatter(self):
        """Test parsing markdown with malformed frontmatter."""
        reader = GitHubRepoReader()
        content = b"""---
title: Test
invalid yaml: [
---
# Content"""

        # Should handle gracefully by returning None
        result = reader._parse_markdown_file(content, "test.md")
        # Malformed YAML will cause parsing to fail, returns None
        assert result is None

    def test_parse_markdown_file_empty_content(self):
        """Test parsing empty markdown file."""
        reader = GitHubRepoReader()
        content = b""

        result = reader._parse_markdown_file(content, "empty.md")

        assert result is not None
        assert result["filename"] == "empty.md"

    def test_session_headers(self):
        """Test that session has proper headers."""
        reader = GitHubRepoReader()
        assert "User-Agent" in reader.session.headers
        assert "repo-sage" in reader.session.headers["User-Agent"]

    def test_close_method(self):
        """Test the close method."""
        reader = GitHubRepoReader()
        reader.close()
        # Session should be closed (we can't easily test this, but ensure no error)
