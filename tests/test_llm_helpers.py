"""Tests for LLM helpers."""

import os
from unittest.mock import Mock, patch

import pytest


class TestOpenAIHelper:
    """Tests for OpenAIHelper class."""

    @patch.dict(
        os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": ""}, clear=False
    )
    @patch("openai.OpenAI")
    def test_initialization_with_env_key(self, mock_openai_client):
        """Test initialization with API key from environment."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_openai_client.return_value = Mock()

        helper = OpenAIHelper()

        assert helper.api_key == "test-key"
        assert helper.model == "gpt-4o-mini"
        mock_openai_client.assert_called_once_with(api_key="test-key")

    @patch.dict(os.environ, {"OPENAI_BASE_URL": ""}, clear=False)
    @patch("openai.OpenAI")
    def test_initialization_with_explicit_key(self, mock_openai_client):
        """Test initialization with explicitly provided API key."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_openai_client.return_value = Mock()

        helper = OpenAIHelper(api_key="explicit-key", model="gpt-4")

        assert helper.api_key == "explicit-key"
        assert helper.model == "gpt-4"
        mock_openai_client.assert_called_once_with(api_key="explicit-key")

    @patch("openai.OpenAI")
    def test_initialization_with_base_url(self, mock_openai_client):
        """Test initialization with custom base URL (e.g., OpenRouter)."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_openai_client.return_value = Mock()

        helper = OpenAIHelper(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="anthropic/claude-3-sonnet",
        )

        assert helper.api_key == "test-key"
        assert helper.base_url == "https://openrouter.ai/api/v1"
        assert helper.model == "anthropic/claude-3-sonnet"
        mock_openai_client.assert_called_once_with(
            api_key="test-key", base_url="https://openrouter.ai/api/v1"
        )

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": "https://custom.api/v1"},
    )
    @patch("openai.OpenAI")
    def test_initialization_with_env_base_url(self, mock_openai_client):
        """Test initialization with base URL from environment."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_openai_client.return_value = Mock()

        helper = OpenAIHelper()

        assert helper.base_url == "https://custom.api/v1"
        mock_openai_client.assert_called_once_with(
            api_key="test-key", base_url="https://custom.api/v1"
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_initialization_without_key_raises_error(self):
        """Test that initialization fails without API key."""
        from repo_sage.llm_helpers import OpenAIHelper

        with pytest.raises(ValueError, match="OpenAI API key not provided"):
            OpenAIHelper()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_generate_basic(self, mock_openai_client):
        """Test basic text generation."""
        from repo_sage.llm_helpers import OpenAIHelper

        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated text"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        helper = OpenAIHelper()
        result = helper.generate("Test prompt")

        assert result == "Generated text"
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4o-mini"
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["content"] == "Test prompt"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_generate_with_system_message(self, mock_openai_client):
        """Test generation with system message."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        helper = OpenAIHelper()
        result = helper.generate("Prompt", system_message="System instructions")

        assert result == "Response"
        call_args = mock_client.chat.completions.create.call_args[1]
        assert len(call_args["messages"]) == 2
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][0]["content"] == "System instructions"
        assert call_args["messages"][1]["role"] == "user"

    @patch.dict(
        os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_BASE_URL": ""}, clear=False
    )
    @patch("openai.OpenAI")
    def test_generate_with_custom_params(self, mock_openai_client):
        """Test generation with custom parameters."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        helper = OpenAIHelper(temperature=0.5, max_tokens=1000)
        helper.generate("Prompt", temperature=0.8)

        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["temperature"] == 0.8  # Overridden
        assert call_args["max_tokens"] == 1000

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_generate_api_error(self, mock_openai_client):
        """Test handling of API errors."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai_client.return_value = mock_client

        helper = OpenAIHelper()

        with pytest.raises(Exception, match="API error"):
            helper.generate("Prompt")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_chunk_document(self, mock_openai_client):
        """Test document chunking."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="## Section 1\nContent"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        helper = OpenAIHelper()
        result = helper.chunk_document("Document text")

        assert result == "## Section 1\nContent"
        call_args = mock_client.chat.completions.create.call_args[1]
        assert "Document text" in call_args["messages"][1]["content"]

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_chunk_document_custom_prompt(self, mock_openai_client):
        """Test document chunking with custom prompt."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        helper = OpenAIHelper()
        custom_prompt = "Split this: {document}"
        result = helper.chunk_document("Doc", custom_prompt=custom_prompt)

        assert result == "Result"
        call_args = mock_client.chat.completions.create.call_args[1]
        assert "Split this: Doc" in call_args["messages"][1]["content"]

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_chunk_document_invalid_custom_prompt(self, mock_openai_client):
        """Test that invalid custom prompt raises error."""
        from repo_sage.llm_helpers import OpenAIHelper

        mock_openai_client.return_value = Mock()

        helper = OpenAIHelper()

        with pytest.raises(ValueError, match="must contain {document}"):
            helper.chunk_document("Doc", custom_prompt="No placeholder")


class TestHelperFunctions:
    """Tests for helper functions."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_create_openai_chunking_function(self, mock_openai_client):
        """Test creating OpenAI chunking function."""
        from repo_sage.llm_helpers import create_openai_chunking_function

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        func = create_openai_chunking_function(model="gpt-4")

        assert callable(func)
        result = func("Test prompt")
        assert result == "Result"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_create_openai_chunking_function_with_base_url(self, mock_openai_client):
        """Test creating OpenAI chunking function with custom base URL."""
        from repo_sage.llm_helpers import create_openai_chunking_function

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="OpenRouter Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        func = create_openai_chunking_function(
            base_url="https://openrouter.ai/api/v1", model="anthropic/claude-3-haiku"
        )

        assert callable(func)
        result = func("Test prompt")
        assert result == "OpenRouter Result"

        # Verify base_url was passed to OpenAI client
        mock_openai_client.assert_called_with(
            api_key="test-key", base_url="https://openrouter.ai/api/v1"
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_get_openai_llm_function(self, mock_openai_client):
        """Test get_openai_llm_function convenience function."""
        from repo_sage.llm_helpers import get_openai_llm_function

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        func = get_openai_llm_function()

        assert callable(func)
        result = func("Test")
        assert result == "Result"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("openai.OpenAI")
    def test_integration_with_chunking_strategy(self, mock_openai_client):
        """Test integration with IntelligentChunkingStrategy."""
        from repo_sage.chunking import DocumentChunker, IntelligentChunkingStrategy
        from repo_sage.llm_helpers import create_openai_chunking_function

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="## Section 1\nContent\n---\n## Section 2\nMore"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        # Create LLM function
        llm_func = create_openai_chunking_function()

        # Use with strategy
        strategy = IntelligentChunkingStrategy(llm_function=llm_func)
        chunker = DocumentChunker(strategy)

        documents = [{"content": "Test document", "filename": "test.md"}]
        chunks = chunker.chunk_documents(documents)

        assert len(chunks) == 2
        assert "Section 1" in chunks[0].content
        assert "Section 2" in chunks[1].content
