"""Unit tests for custom exceptions."""

import pytest

from repo_sage.exceptions import (
    FileParsingError,
    InvalidRepositoryError,
    RepoSageException,
    RepositoryDownloadError,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_base_exception(self):
        """Test base RepoSageException."""
        exc = RepoSageException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_repository_download_error(self):
        """Test RepositoryDownloadError."""
        exc = RepositoryDownloadError("Download failed")
        assert str(exc) == "Download failed"
        assert isinstance(exc, RepoSageException)
        assert isinstance(exc, Exception)

    def test_file_parsing_error(self):
        """Test FileParsingError."""
        exc = FileParsingError("Parse failed")
        assert str(exc) == "Parse failed"
        assert isinstance(exc, RepoSageException)

    def test_invalid_repository_error(self):
        """Test InvalidRepositoryError."""
        exc = InvalidRepositoryError("Invalid repo")
        assert str(exc) == "Invalid repo"
        assert isinstance(exc, RepoSageException)

    def test_exception_raising(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(RepositoryDownloadError):
            raise RepositoryDownloadError("Test")

        with pytest.raises(FileParsingError):
            raise FileParsingError("Test")

        with pytest.raises(InvalidRepositoryError):
            raise InvalidRepositoryError("Test")

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        # All custom exceptions should be catchable as RepoSageException
        try:
            raise RepositoryDownloadError("Test")
        except RepoSageException:
            pass

        try:
            raise FileParsingError("Test")
        except RepoSageException:
            pass

        try:
            raise InvalidRepositoryError("Test")
        except RepoSageException:
            pass
