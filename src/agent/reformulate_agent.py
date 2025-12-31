"""Query reformulation agent using PydanticAI."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from src.config import settings


class ReformulationResult(BaseModel):
    """Structured output for query reformulation."""

    reformulated: str = Field(
        description="The clarified query (or original if already clear)"
    )
    was_changed: bool = Field(
        description="True if the query was reformulated, False if passed through unchanged"
    )


def _create_model() -> OpenAIModel:
    """Create OpenAI model configured for Ollama."""
    base_url = settings.ollama_base_url
    if not base_url.endswith("/v1"):
        base_url = f"{base_url.rstrip('/')}/v1"

    # Use explicit client configuration instead of environment variables
    client = AsyncOpenAI(
        base_url=base_url,
        api_key="ollama",
    )
    return OpenAIModel(settings.ollama_fast_model, openai_client=client)


# Lazy-initialized agent (created on first access)
_reformulate_agent = None


def get_reformulate_agent() -> Agent:
    """Get or create the reformulation agent."""
    global _reformulate_agent

    if _reformulate_agent is None:
        _reformulate_agent = Agent(
            model=_create_model(),
            output_type=ReformulationResult,
            system_prompt="""You are a query reformulation assistant for a powerlifting coach AI.

RULES:
1. If the input is CLEAR and UNAMBIGUOUS → return it UNCHANGED
2. Only reformulate if truly ambiguous (vague pronouns like "that", "it" without context, or incomplete requests)
3. Keep reformulations concise and in the same language as the input
4. Preserve the user's intent exactly

Examples:
- "Hello!" → UNCHANGED (clear greeting)
- "What is my PR?" → UNCHANGED (clear request)
- "that thing" → "Could you clarify what you're referring to?"
- "do it again" → "Could you clarify what action you'd like me to repeat?"
- "150kg plates" → "Calculate the plates needed for 150kg"

Return the reformulated query (or original if clear) and whether you changed it.""",
        )

    return _reformulate_agent
