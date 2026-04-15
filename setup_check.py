#!/usr/bin/env python3
"""Setup helper script for repo-sage."""

from pathlib import Path


def check_env_file() -> bool:
    """Check if .env file exists and has required keys."""
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        print("❌ .env file not found!")
        print("\n📝 Creating .env file from .env.example...")

        if env_example.exists():
            # Copy example file
            content = env_example.read_text()
            env_file.write_text(content)
            print("✅ Created .env file")
            print("\n⚠️  Please edit .env and add your API keys!")
        else:
            print("❌ .env.example not found")
            return False

    # Check for required keys
    env_content = env_file.read_text()

    required = {"OPENAI_API_KEY": False}
    optional = {"HF_TOKEN": False, "OPENAI_BASE_URL": False}

    for line in env_content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            for key in required:
                if line.startswith(key + "=") and "your_" not in line:
                    required[key] = True
            for key in optional:
                if line.startswith(key + "=") and "your_" not in line:
                    optional[key] = True

    print("\n" + "=" * 70)
    print("ENVIRONMENT SETUP CHECK")
    print("=" * 70)

    print("\n📋 Required Configuration:")
    for key, found in required.items():
        status = "✅" if found else "❌"
        print(f"{status} {key}: {'SET' if found else 'NOT SET'}")

    print("\n📋 Optional Configuration:")
    for key, found in optional.items():
        status = "✅" if found else "⚠️ "
        print(f"{status} {key}: {'SET' if found else 'NOT SET (optional)'}")

    if optional["HF_TOKEN"]:
        print("\n✅ HF_TOKEN is set - You won't see HuggingFace warnings")
    else:
        print("\n⚠️  HF_TOKEN not set - You may see warnings when loading models")
        print("   Get a free token at: https://huggingface.co/settings/tokens")
        print("   Add to .env file: HF_TOKEN=your_token_here")

    print("\n" + "=" * 70)

    if not all(required.values()):
        print("\n❌ Missing required configuration!")
        print("   Please edit .env and set all required keys")
        return False

    print("\n✅ Configuration complete!")
    return True


def test_imports() -> bool:
    """Test if all required packages are installed."""
    print("\n" + "=" * 70)
    print("PACKAGE INSTALLATION CHECK")
    print("=" * 70 + "\n")

    packages = {
        "sentence_transformers": "sentence-transformers",
        "minsearch": "minsearch",
        "pydantic_ai": "pydantic-ai",
        "openai": "openai",
        "dotenv": "python-dotenv",
    }

    all_installed = True

    for module, package in packages.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_installed = False

    if not all_installed:
        print("\n❌ Missing packages!")
        print("   Run: uv pip install -e '.[dev]'")
        return False

    print("\n✅ All packages installed!")
    return True


def main() -> None:
    """Run all setup checks."""
    print("🚀 repo-sage Setup Check\n")

    env_ok = check_env_file()
    packages_ok = test_imports()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if env_ok and packages_ok:
        print("\n✅ Setup complete! You're ready to use repo-sage!")
        print("\nQuick start:")
        print("  python examples_search.py")
        print("  python examples_agent.py  (requires OPENAI_API_KEY)")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
