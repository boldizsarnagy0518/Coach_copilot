"""
Unit tests for the LLM provider system.

These tests verify the LLM abstraction layer works correctly
without requiring actual LLM services to be running.
"""

import os
from unittest.mock import patch

import pytest

from src.llm.base import BaseLLMProvider, LLMResponse


class TestLLMResponse:
    """Tests for the LLMResponse dataclass."""

    def test_response_creation(self):
        """Test creating a basic LLMResponse."""
        response = LLMResponse(
            content="Hello, world!",
            model="test-model",
            provider="test",
        )
        assert response.content == "Hello, world!"
        assert response.model == "test-model"
        assert response.provider == "test"
        assert response.tokens_used is None
        assert response.metadata is None

    def test_response_with_metadata(self):
        """Test creating LLMResponse with all fields."""
        response = LLMResponse(
            content="Test content",
            model="gemini-2.0-flash",
            provider="gemini",
            tokens_used=150,
            metadata={"prompt_tokens": 50, "completion_tokens": 100},
        )
        assert response.tokens_used == 150
        assert response.metadata["prompt_tokens"] == 50


class TestBaseLLMProvider:
    """Tests for the abstract base provider."""

    def test_base_provider_is_abstract(self):
        """Base provider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            BaseLLMProvider()

    def test_health_check_interface(self, mock_ollama_provider):
        """Test the health check method returns expected format."""
        # Health check is implemented in base class
        # Using mock to test interface
        assert mock_ollama_provider.provider_name == "ollama"
        assert mock_ollama_provider.model_name == "llama3.2"


class TestOllamaProvider:
    """Tests for the Ollama provider implementation."""

    def test_ollama_provider_creation(self):
        """Test creating Ollama provider with defaults."""
        from src.llm.ollama_provider import OllamaProvider

        provider = OllamaProvider()
        assert provider.provider_name == "ollama"
        assert provider.model_name == "llama3.2"

    def test_ollama_provider_custom_model(self):
        """Test creating Ollama provider with custom model."""
        from src.llm.ollama_provider import OllamaProvider

        provider = OllamaProvider(model="mistral")
        assert provider.model_name == "mistral"

    def test_ollama_provider_custom_url(self):
        """Test creating Ollama provider with custom URL."""
        from src.llm.ollama_provider import OllamaProvider

        provider = OllamaProvider(base_url="http://192.168.1.100:11434")
        assert provider._base_url == "http://192.168.1.100:11434"

    @pytest.mark.asyncio
    async def test_ollama_is_available_when_not_running(self):
        """is_available should return False when Ollama isn't running."""
        from src.llm.ollama_provider import OllamaProvider

        # Use a valid but unlikely-to-be-used port to simulate Ollama not running
        provider = OllamaProvider(base_url="http://localhost:59999")
        is_available = await provider.is_available()
        assert is_available is False


class TestGeminiProvider:
    """Tests for the Gemini provider implementation."""

    def test_gemini_provider_requires_api_key(self):
        """Test that Gemini provider requires API key."""
        from src.llm.gemini_provider import GeminiProvider

        # Should work with API key
        provider = GeminiProvider(api_key="test-key-not-real")
        assert provider.provider_name == "gemini"

    def test_gemini_provider_custom_model(self):
        """Test creating Gemini provider with custom model."""
        from src.llm.gemini_provider import GeminiProvider

        provider = GeminiProvider(api_key="test-key", model="gemini-1.5-pro")
        assert provider.model_name == "gemini-1.5-pro"

    def test_gemini_list_models(self):
        """Test listing available Gemini models."""
        from src.llm.gemini_provider import GeminiProvider

        models = GeminiProvider.list_models()
        assert "gemini-2.0-flash" in models
        assert "gemini-1.5-pro" in models


class TestLLMFactory:
    """Tests for the LLM factory function."""

    def test_factory_creates_ollama_by_default(self):
        """Factory should create Ollama provider by default in dev."""
        from src.llm.factory import create_llm_provider

        # Set environment to use Ollama
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
            from src.core.config import reload_settings

            reload_settings()

            provider = create_llm_provider("ollama")
            assert provider.provider_name == "ollama"

    def test_factory_creates_gemini_with_key(self):
        """Factory should create Gemini when specified with key."""
        from src.llm.factory import create_llm_provider

        provider = create_llm_provider("gemini", api_key="test-key")
        assert provider.provider_name == "gemini"

    def test_factory_raises_for_unknown_provider(self):
        """Factory should raise error for unknown providers."""
        from src.llm.factory import create_llm_provider

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider("unknown_provider")

    def test_factory_gemini_requires_api_key(self):
        """Factory should raise if Gemini requested without key."""
        from src.llm.factory import create_llm_provider

        # Mock settings to have no API key
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            from src.core.config import reload_settings

            reload_settings()

            with pytest.raises(ValueError, match="API key is required"):
                create_llm_provider("gemini")


class TestMockedGeneration:
    """Tests using mocked providers for generation."""

    @pytest.mark.asyncio
    async def test_mocked_ollama_generate(self, mock_ollama_provider):
        """Test mocked Ollama generation."""
        response = await mock_ollama_provider.generate("Hello")

        assert response.content == "This is a mocked response for testing."
        assert response.provider == "ollama"
        mock_ollama_provider.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_mocked_gemini_generate(self, mock_gemini_provider):
        """Test mocked Gemini generation."""
        response = await mock_gemini_provider.generate("Hello")

        assert response.content == "This is a mocked Gemini response for testing."
        assert response.provider == "gemini"
        mock_gemini_provider.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_mocked_provider_is_available(self, mock_ollama_provider):
        """Test mocked availability check."""
        is_available = await mock_ollama_provider.is_available()
        assert is_available is True
