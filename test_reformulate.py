import asyncio
from src.agent.reformulate_agent import get_reformulate_agent, ReformulationResult


async def test_agent():
    print("Initializing agent...")
    agent = get_reformulate_agent()
    print("Agent initialized successfully.")

    # We won't run a query to avoid needing running Ollama (or we can try if it's running)
    # Just init is enough to verify if _create_model fails.
    # Provider is stored in _provider or similar, checking internal for verification
    provider = getattr(agent.model, "provider", getattr(agent.model, "_provider", None))
    print("Agent model provider configured:", provider)
    if hasattr(provider, "client"):
        print("Provider has client attribute: Yes")
    else:
        print("Provider has client attribute: No")


if __name__ == "__main__":
    asyncio.run(test_agent())
