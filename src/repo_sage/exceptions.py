"""Custom exceptions for repo-sage."""


class RepoSageException(Exception):
    """Base exception for repo-sage."""

    pass


class RepositoryDownloadError(RepoSageException):
    """Raised when repository download fails."""

    pass


class FileParsingError(RepoSageException):
    """Raised when file parsing fails."""

    pass


class InvalidRepositoryError(RepoSageException):
    """Raised when repository information is invalid."""

    pass


class ChunkingError(RepoSageException):
    """Raised when document chunking fails."""

    pass
