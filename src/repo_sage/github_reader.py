"""GitHub repository data reader with markdown file extraction."""

import io
import logging
import zipfile
from typing import Any

import frontmatter
import requests

from .exceptions import InvalidRepositoryError, RepositoryDownloadError

# Configure module logger
logger = logging.getLogger(__name__)

# Constants
GITHUB_CODELOAD_PREFIX = "https://codeload.github.com"
DEFAULT_BRANCH = "main"
MARKDOWN_EXTENSIONS: set[str] = {".md", ".mdx"}
REQUEST_TIMEOUT = 30  # seconds
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class GitHubRepoReader:
    """
    A class to download and parse markdown files from GitHub repositories.

    This class provides methods to download a GitHub repository as a zip file
    and extract markdown files with frontmatter metadata.
    """

    def __init__(
        self,
        timeout: int = REQUEST_TIMEOUT,
        max_file_size: int = MAX_FILE_SIZE,
    ):
        """
        Initialize the GitHubRepoReader.

        Args:
            timeout: Request timeout in seconds
            max_file_size: Maximum file size to process in bytes
        """
        self.timeout = timeout
        self.max_file_size = max_file_size
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "repo-sage/0.1.0",
            }
        )

    def __enter__(self) -> "GitHubRepoReader":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - clean up resources."""
        self.close()

    def close(self) -> None:
        """Close the HTTP session."""
        if hasattr(self, "session"):
            self.session.close()

    def _validate_inputs(
        self,
        repo_owner: str,
        repo_name: str,
        branch_name: str,
    ) -> None:
        """
        Validate repository inputs.

        Args:
            repo_owner: GitHub username or organization
            repo_name: Repository name
            branch_name: Branch name

        Raises:
            InvalidRepositoryError: If inputs are invalid
        """
        if not repo_owner or not isinstance(repo_owner, str):
            raise InvalidRepositoryError("repo_owner must be a non-empty string")

        if not repo_name or not isinstance(repo_name, str):
            raise InvalidRepositoryError("repo_name must be a non-empty string")

        if not branch_name or not isinstance(branch_name, str):
            raise InvalidRepositoryError("branch_name must be a non-empty string")

        # Check for invalid characters
        invalid_chars = set('<>:"|?*')
        if any(
            char in repo_owner or char in repo_name or char in branch_name
            for char in invalid_chars
        ):
            raise InvalidRepositoryError(
                "Repository parameters contain invalid characters"
            )

    def _build_download_url(
        self,
        repo_owner: str,
        repo_name: str,
        branch_name: str,
    ) -> str:
        """
        Build the GitHub download URL.

        Args:
            repo_owner: GitHub username or organization
            repo_name: Repository name
            branch_name: Branch name

        Returns:
            Complete download URL
        """
        return f"{GITHUB_CODELOAD_PREFIX}/{repo_owner}/{repo_name}/zip/refs/heads/{branch_name}"

    def _download_repository(self, url: str) -> bytes:
        """
        Download repository as zip file.

        Args:
            url: Download URL

        Returns:
            Repository zip file content

        Raises:
            RepositoryDownloadError: If download fails
        """
        try:
            logger.info(f"Downloading repository from: {url}")
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 404:
                raise RepositoryDownloadError(f"Repository not found (404): {url}")
            elif response.status_code == 403:
                raise RepositoryDownloadError(
                    f"Access forbidden (403): {url}. Check if repository is private."
                )
            elif response.status_code != 200:
                raise RepositoryDownloadError(
                    f"Failed to download repository (HTTP {response.status_code}): {url}"
                )

            logger.info(f"Successfully downloaded {len(response.content)} bytes")
            return response.content

        except requests.exceptions.Timeout as e:
            raise RepositoryDownloadError(
                f"Download timeout after {self.timeout}s"
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise RepositoryDownloadError(
                f"Connection error while downloading: {url}"
            ) from e
        except requests.exceptions.RequestException as e:
            raise RepositoryDownloadError(f"Download failed: {str(e)}") from e

    def _is_markdown_file(self, filename: str) -> bool:
        """
        Check if a file is a markdown file based on extension.

        Args:
            filename: File name to check

        Returns:
            True if file is markdown, False otherwise
        """
        return any(filename.lower().endswith(ext) for ext in MARKDOWN_EXTENSIONS)

    def _parse_markdown_file(
        self,
        file_content: bytes,
        filename: str,
    ) -> dict[str, Any] | None:
        """
        Parse a markdown file and extract frontmatter.

        Args:
            file_content: Raw file content
            filename: Name of the file

        Returns:
            Dictionary with file content and metadata, or None if parsing fails
        """
        try:
            # Decode content
            content = file_content.decode("utf-8", errors="ignore")

            # Parse frontmatter
            post = frontmatter.loads(content)
            data: dict[str, Any] = post.to_dict()
            data["filename"] = filename

            logger.debug(f"Successfully parsed: {filename}")
            return data

        except Exception as e:
            logger.warning(f"Error parsing {filename}: {e}")
            return None

    def _extract_markdown_files(
        self,
        zip_content: bytes,
    ) -> list[dict[str, Any]]:
        """
        Extract and parse markdown files from zip content.

        Args:
            zip_content: Zip file content

        Returns:
            List of dictionaries containing file content and metadata

        Raises:
            RepositoryDownloadError: If zip extraction fails
        """
        repository_data = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                markdown_files = [
                    f
                    for f in zf.infolist()
                    if self._is_markdown_file(f.filename) and not f.is_dir()
                ]

                logger.info(f"Found {len(markdown_files)} markdown files")

                for file_info in markdown_files:
                    # Skip files that are too large
                    if file_info.file_size > self.max_file_size:
                        logger.warning(
                            f"Skipping {file_info.filename}: "
                            f"file too large ({file_info.file_size} bytes)"
                        )
                        continue

                    try:
                        with zf.open(file_info) as f_in:
                            file_content = f_in.read()

                        parsed_data = self._parse_markdown_file(
                            file_content,
                            file_info.filename,
                        )

                        if parsed_data:
                            repository_data.append(parsed_data)

                    except Exception as e:
                        logger.warning(f"Error processing {file_info.filename}: {e}")
                        continue

                logger.info(f"Successfully parsed {len(repository_data)} files")

        except zipfile.BadZipFile as e:
            raise RepositoryDownloadError("Invalid zip file content") from e
        except Exception as e:
            raise RepositoryDownloadError(f"Error extracting zip: {str(e)}") from e

        return repository_data

    def read_repo_data(
        self,
        repo_owner: str,
        repo_name: str,
        branch_name: str = DEFAULT_BRANCH,
    ) -> list[dict[str, Any]]:
        """
        Download and parse all markdown files from a GitHub repository.

        Args:
            repo_owner: GitHub username or organization
            repo_name: Repository name
            branch_name: Branch name (defaults to 'main')

        Returns:
            List of dictionaries containing file content and metadata

        Raises:
            InvalidRepositoryError: If repository parameters are invalid
            RepositoryDownloadError: If download or extraction fails

        Example:
            >>> reader = GitHubRepoReader()
            >>> data = reader.read_repo_data("octocat", "Hello-World")
            >>> print(f"Found {len(data)} markdown files")
        """
        # Validate inputs
        self._validate_inputs(repo_owner, repo_name, branch_name)

        # Build URL
        url = self._build_download_url(repo_owner, repo_name, branch_name)

        # Download repository
        zip_content = self._download_repository(url)

        # Extract and parse markdown files
        repository_data = self._extract_markdown_files(zip_content)

        return repository_data


def read_repo_data(
    repo_owner: str,
    repo_name: str,
    branch_name: str = DEFAULT_BRANCH,
) -> list[dict[str, Any]]:
    """
    Download and parse all markdown files from a GitHub repository.

    This is a convenience function that creates a GitHubRepoReader instance
    and calls its read_repo_data method.

    Args:
        repo_owner: GitHub username or organization
        repo_name: Repository name
        branch_name: Branch name (defaults to 'main')

    Returns:
        List of dictionaries containing file content and metadata

    Raises:
        InvalidRepositoryError: If repository parameters are invalid
        RepositoryDownloadError: If download or extraction fails

    Example:
        >>> data = read_repo_data("octocat", "Hello-World")
        >>> print(f"Found {len(data)} markdown files")
    """
    with GitHubRepoReader() as reader:
        result: list[dict[str, Any]] = reader.read_repo_data(
            repo_owner, repo_name, branch_name
        )
        return result
