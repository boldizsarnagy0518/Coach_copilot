"""
Pytest configuration and shared fixtures for Coach Copilot tests.
"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest


# Set test environment before importing settings
os.environ["ENVIRONMENT"] = "development"
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["DEBUG"] = "true"


@pytest.fixture
def mock_settings():
    """
    Fixture providing mock settings for tests.

    This avoids needing real API keys or .env file during testing.
    """
    from src.core.settings import Settings

    return Settings(
        llm_provider="ollama",
        ollama_model="llama3.2",
        ollama_base_url="http://localhost:11434",
        environment="development",
        debug=True,
    )


@pytest.fixture
def mock_ollama_provider():
    """
    Fixture providing a mocked Ollama provider.

    Useful for testing components that depend on LLM without
    requiring a running Ollama instance.
    """
    from src.llm.base import LLMResponse

    mock = MagicMock()
    mock.provider_name = "ollama"
    mock.model_name = "llama3.2"

    # Mock generate method
    async def mock_generate(*args, **kwargs):
        return LLMResponse(
            content="This is a mocked response for testing.",
            model="llama3.2",
            provider="ollama",
            tokens_used=50,
        )

    mock.generate = AsyncMock(side_effect=mock_generate)
    mock.is_available = AsyncMock(return_value=True)

    return mock


@pytest.fixture
def mock_gemini_provider():
    """
    Fixture providing a mocked Gemini provider.

    Useful for testing components that depend on Gemini API
    without requiring real API credentials.
    """
    from src.llm.base import LLMResponse

    mock = MagicMock()
    mock.provider_name = "gemini"
    mock.model_name = "gemini-2.0-flash"

    # Mock generate method
    async def mock_generate(*args, **kwargs):
        return LLMResponse(
            content="This is a mocked Gemini response for testing.",
            model="gemini-2.0-flash",
            provider="gemini",
            tokens_used=100,
        )

    mock.generate = AsyncMock(side_effect=mock_generate)
    mock.is_available = AsyncMock(return_value=True)

    return mock


@pytest.fixture
def calculator():
    """Fixture providing a PowerliftingCalculator instance."""
    from src.tools.calculator import PowerliftingCalculator

    return PowerliftingCalculator()


@pytest.fixture
def plate_calculator():
    """Fixture providing a PlateCalculator instance."""
    from src.tools.calculator import PlateCalculator

    return PlateCalculator()


@pytest.fixture
def sample_athlete_data():
    """
    Fixture providing sample athlete data for testing.
    """
    return {
        "name": "Test Athlete",
        "bodyweight": 83.0,
        "gender": "male",
        "squat": 200.0,
        "bench": 140.0,
        "deadlift": 240.0,
        "total": 580.0,
    }
