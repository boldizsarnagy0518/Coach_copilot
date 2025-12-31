import instructor
from openai import OpenAI
from src.config import settings


def get_instructor_client():
    """
    Returns an OpenAI client patched by Instructor for structured output.
    Configured to point to the Ollama instance defined in settings.
    """

    # Ensure URL ends with /v1 for OpenAI client compatibility
    base_url = settings.ollama_base_url
    if not base_url.endswith("/v1"):
        base_url = f"{base_url.rstrip('/')}/v1"

    client = instructor.from_openai(
        OpenAI(
            base_url=base_url,
            api_key="ollama",  # required but ignored by Ollama
        ),
        mode=instructor.Mode.JSON,
    )
    return client
