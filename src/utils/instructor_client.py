"""Instructor client for structured LLM outputs with Ollama."""

import instructor
from openai import OpenAI
from src.config import settings

# Cached client instance (singleton pattern)
_instructor_client = None


def get_instructor_client():
    """
    Returns an OpenAI client patched by Instructor for structured output.
    Configured to point to the Ollama instance defined in settings.

    The client is cached after first creation for better performance.
    """
    global _instructor_client

    if _instructor_client is not None:
        return _instructor_client

    # Ensure URL ends with /v1 for OpenAI client compatibility
    base_url = settings.ollama_base_url
    if not base_url.endswith("/v1"):
        base_url = f"{base_url.rstrip('/')}/v1"

    _instructor_client = instructor.from_openai(
        OpenAI(
            base_url=base_url,
            api_key="ollama",
        ),
        mode=instructor.Mode.JSON,
    )
    return _instructor_client
