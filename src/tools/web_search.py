"""Web search tool with LangChain decorator."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """Input for web search."""

    query: str = Field(description="Search query")


@tool(args_schema=WebSearchInput)
def search_web(query: str) -> str:
    """Search the web for information. Use when local knowledge is insufficient or user asks about recent events."""
    try:
        from duckduckgo_search import DDGS

        results = list(DDGS().text(query, max_results=3))

        if not results:
            return f"No results found for: {query}"

        formatted = []
        for r in results:
            formatted.append(
                f"- {r.get('title', 'No title')}: {r.get('body', '')[:200]}..."
            )

        return f"Web search results for '{query}':\n" + "\n".join(formatted)
    except Exception as e:
        return f"Web search failed: {e}"


# Export all tools
ALL_TOOLS = [search_web]
