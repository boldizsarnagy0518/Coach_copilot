"""Web search and crawl tools with LangChain decorator."""

from datetime import datetime, date
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


class CrawlUrlInput(BaseModel):
    """Input for URL crawling."""

    url: str = Field(description="URL to crawl and extract content from")


@tool(args_schema=CrawlUrlInput)
def crawl_url(url: str) -> str:
    """Crawl a specific URL and extract its content. Use when you need detailed information from a specific webpage."""
    try:
        from langchain_community.document_loaders import WebBaseLoader

        loader = WebBaseLoader(url)
        docs = loader.load()

        if not docs:
            return f"No content found at: {url}"

        # Combine and truncate content
        content = "\n\n".join(doc.page_content for doc in docs)
        # Limit to first 3000 chars to avoid overwhelming context
        if len(content) > 3000:
            content = content[:3000] + "...[truncated]"

        return f"Content from {url}:\n\n{content}"
    except Exception as e:
        return f"Failed to crawl {url}: {e}"


class CompetitionCountdownInput(BaseModel):
    """Input for competition countdown."""

    competition_date: str = Field(
        description="Competition date in YYYY-MM-DD format (e.g., 2025-03-15)"
    )
    competition_name: str = Field(
        default="Competition", description="Name of the competition (optional)"
    )


@tool(args_schema=CompetitionCountdownInput)
def competition_countdown(
    competition_date: str, competition_name: str = "Competition"
) -> str:
    """Calculate days until a powerlifting competition. Helps with peaking and preparation planning."""
    try:
        comp_date = datetime.strptime(competition_date, "%Y-%m-%d").date()
        today = date.today()

        delta = comp_date - today
        days_left = delta.days

        if days_left < 0:
            return f"⚠️ {competition_name} was {abs(days_left)} days ago ({comp_date.strftime('%B %d, %Y')})"

        if days_left == 0:
            return f"🏆 {competition_name} is TODAY! Good luck! 💪"

        # Calculate weeks and remaining days
        weeks = days_left // 7
        remaining_days = days_left % 7

        # Peaking advice
        if days_left <= 7:
            phase = "🔴 PEAK WEEK - Taper intensity, rest, stay sharp"
        elif days_left <= 14:
            phase = "🟠 2 weeks out - Final heavy singles, start reducing volume"
        elif days_left <= 21:
            phase = "🟡 3 weeks out - Last heavy week, peak openers"
        elif days_left <= 42:
            phase = "🟢 4-6 weeks out - Build to peak weights"
        else:
            phase = "💪 Training block - Focus on volume and strength building"

        time_str = (
            f"{weeks} weeks, {remaining_days} days"
            if weeks > 0
            else f"{days_left} days"
        )

        return f"""📅 **{competition_name}** - {comp_date.strftime("%B %d, %Y")}

⏱️ **{time_str}** until competition ({days_left} total days)

{phase}"""

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-03-15)"
    except Exception as e:
        return f"Error calculating countdown: {e}"


# Export all tools
ALL_TOOLS = [search_web, crawl_url, competition_countdown]
