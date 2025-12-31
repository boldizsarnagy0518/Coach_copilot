from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from src.config import settings


class ReformulationResult(BaseModel):
    reformulated: str = Field(
        description="The clarified query (or original if already clear)"
    )
    was_changed: bool = Field(
        description="True if the query was reformulated, False if passed through unchanged"
    )


# Configure Ollama model via OpenAI compatibility
model_name = settings.ollama_fast_model
base_url = settings.ollama_base_url
if not base_url.endswith("/v1"):
    base_url = f"{base_url.rstrip('/')}/v1"

model = OpenAIModel(
    model_name=model_name,
    base_url=base_url,
    api_key="ollama",
)

reformulate_agent = Agent(
    model,
    result_type=ReformulationResult,
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
