# Makefile for repo-sage development

.PHONY: help install install-dev test test-unit test-integration coverage lint format clean pre-commit-install pre-commit-run

PYTEST = .venv/bin/pytest

help:
	@echo "Available commands:"
	@echo "  make install          - Install package dependencies"
	@echo "  make install-dev      - Install package with dev dependencies"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run   - Run pre-commit on all files"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only (skip integration tests)"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make lint             - Run code linting (ruff)"
	@echo "  make format           - Format code with black"
	@echo "  make type-check       - Run type checking with mypy"
	@echo "  make clean            - Remove build artifacts and cache"
	@echo "  make run              - Run the example script"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"
	@echo ""
	@echo "✅ Dev dependencies installed!"
	@echo "💡 Run 'make pre-commit-install' to set up git hooks"

pre-commit-install:
	.venv/bin/pre-commit install
	@echo "✅ Pre-commit hooks installed!"
	@echo "Code will be automatically checked before each commit"

pre-commit-run:
	.venv/bin/pre-commit run --all-files

test:
	$(PYTEST)

test-unit:
	$(PYTEST) -m "not integration"

test-integration:
	$(PYTEST) -m integration

coverage:
	$(PYTEST) --cov=src/repo_sage --cov-report=html --cov-report=term-missing

lint:
	.venv/bin/ruff check src/ tests/

format:
	.venv/bin/black src/ tests/
	.venv/bin/ruff check --fix src/ tests/

type-check:
	.venv/bin/mypy src/

run:
	python main.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
