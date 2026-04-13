"""Example usage of repo-sage."""

import logging

from repo_sage import read_repo_data
from repo_sage.exceptions import InvalidRepositoryError, RepositoryDownloadError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """Main entry point demonstrating repo-sage usage."""
    print("=" * 60)
    print("repo-sage: GitHub Repository Data Extraction Tool")
    print("=" * 60)

    # Example 1: Read from a public repository
    try:
        print("\n📥 Downloading repository data...")
        data = read_repo_data("github", "gitignore", "main")

        print(f"\n✅ Successfully extracted {len(data)} markdown files")

        # Display first few files
        print("\n📄 Sample files found:")
        for item in data[:3]:
            filename = item.get("filename", "Unknown")
            title = item.get("title", "No title")
            print(f"  - {filename}")
            if title != "No title":
                print(f"    Title: {title}")

        if len(data) > 3:
            print(f"  ... and {len(data) - 3} more files")

    except InvalidRepositoryError as e:
        print(f"\n❌ Invalid repository: {e}")
    except RepositoryDownloadError as e:
        print(f"\n❌ Download error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
