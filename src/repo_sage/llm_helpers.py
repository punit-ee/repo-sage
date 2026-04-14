"""LLM integration helpers for repo-sage."""

import logging
import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class OpenAIHelper:
    """
    Helper class for OpenAI API integration.

    This class provides a simple interface for making OpenAI API calls
    for document chunking and other text processing tasks.

    Supports OpenAI and OpenAI-compatible APIs (like OpenRouter).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 4000,
        base_url: str | None = None,
    ):
        """
        Initialize OpenAI helper.

        Args:
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
            model: Model to use for completions
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            base_url: Base URL for API (for OpenRouter or other providers)
                     If None, reads from OPENAI_BASE_URL env var or uses OpenAI default

        Raises:
            ValueError: If API key is not provided and not in environment

        Example:
            # For OpenAI (default)
            helper = OpenAIHelper(api_key="sk-...")

            # For OpenRouter
            helper = OpenAIHelper(
                api_key="sk-or-...",
                base_url="https://openrouter.ai/api/v1",
                model="openai/gpt-4o-mini"
            )
        """
        # Import openai here to make it an optional dependency
        try:
            import openai

            self.openai = openai
        except ImportError as e:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install openai"
            ) from e

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Get base URL from parameter or environment
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize client with optional base_url
        client_params = {"api_key": self.api_key}
        if self.base_url:
            client_params["base_url"] = self.base_url
            logger.info(f"Using custom base URL: {self.base_url}")

        self.client = self.openai.OpenAI(**client_params)
        logger.info(f"Initialized OpenAI helper with model: {model}")

    def generate(
        self,
        prompt: str,
        system_message: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate completion from OpenAI.

        Args:
            prompt: User prompt
            system_message: Optional system message
            **kwargs: Additional parameters to pass to OpenAI API

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        messages = []

        if system_message:
            messages.append({"role": "system", "content": system_message})

        messages.append({"role": "user", "content": prompt})

        # Merge kwargs with defaults
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        params.update(kwargs)

        try:
            logger.debug(f"Calling OpenAI API with model: {params['model']}")
            response = self.client.chat.completions.create(**params)
            result = response.choices[0].message.content or ""
            logger.debug(f"Received response: {len(result)} characters")
            return result

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def chunk_document(self, document: str, custom_prompt: str | None = None) -> str:
        """
        Chunk a document using OpenAI.

        Args:
            document: Document text to chunk
            custom_prompt: Optional custom prompt template (must contain {document})

        Returns:
            Chunked document with sections separated by ---

        Raises:
            Exception: If API call fails
        """
        if custom_prompt and "{document}" not in custom_prompt:
            raise ValueError("Custom prompt must contain {document} placeholder")

        prompt_template = custom_prompt or self._get_default_chunking_prompt()
        prompt = prompt_template.format(document=document)

        system_message = (
            "You are an expert at analyzing and structuring technical documentation. "
            "Your task is to split documents into logical, self-contained sections."
        )

        return self.generate(prompt, system_message=system_message)

    @staticmethod
    def _get_default_chunking_prompt() -> str:
        """Get default prompt for document chunking."""
        return """
Split the provided document into logical sections that make sense for a Q&A system.

Each section should be self-contained and cover a specific topic or concept.

<DOCUMENT>
{document}
</DOCUMENT>

Requirements:
1. Each section should have a clear heading (## Section Name)
2. Include all relevant details in each section
3. Make sections comprehensive but focused
4. Separate sections with ---

Use this format:

## Section Name

Section content with all relevant details and context.

---

## Another Section Name

Another section content with complete information.

---
""".strip()


def create_openai_chunking_function(
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
    base_url: str | None = None,
    **kwargs: Any,
) -> Callable[[str], str]:
    """
    Create an OpenAI-based chunking function for use with IntelligentChunkingStrategy.

    Args:
        api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        model: Model to use
        base_url: Base URL for API (for OpenRouter or other providers)
        **kwargs: Additional parameters for OpenAI helper

    Returns:
        Callable function that takes a prompt and returns a string

    Example:
        >>> from repo_sage.llm_helpers import create_openai_chunking_function
        >>> from repo_sage.chunking import IntelligentChunkingStrategy, DocumentChunker
        >>>
        >>> # For OpenAI
        >>> llm_func = create_openai_chunking_function(model="gpt-4o-mini")
        >>>
        >>> # For OpenRouter
        >>> llm_func = create_openai_chunking_function(
        ...     base_url="https://openrouter.ai/api/v1",
        ...     model="openai/gpt-4o-mini"
        ... )
        >>>
        >>> strategy = IntelligentChunkingStrategy(llm_function=llm_func)
        >>> chunker = DocumentChunker(strategy)
    """
    helper = OpenAIHelper(api_key=api_key, model=model, base_url=base_url, **kwargs)

    def chunking_function(prompt: str) -> str:
        """Wrapper function for OpenAI chunking."""
        return helper.generate(prompt)

    return chunking_function


# Convenience function for quick usage
def get_openai_llm_function(
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
    base_url: str | None = None,
) -> Callable[[str], str]:
    """
    Get a simple OpenAI LLM function for chunking.

    This is a convenience wrapper around create_openai_chunking_function.

    Args:
        api_key: OpenAI API key
        model: Model to use
        base_url: Base URL for API (for OpenRouter or other providers)

    Returns:
        Callable LLM function

    Example:
        >>> from repo_sage.llm_helpers import get_openai_llm_function
        >>>
        >>> # For OpenAI
        >>> llm_func = get_openai_llm_function()  # Uses OPENAI_API_KEY from env
        >>>
        >>> # For OpenRouter
        >>> llm_func = get_openai_llm_function(
        ...     base_url="https://openrouter.ai/api/v1",
        ...     model="anthropic/claude-3-sonnet"
        ... )
    """
    return create_openai_chunking_function(
        api_key=api_key, model=model, base_url=base_url
    )
