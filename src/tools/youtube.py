"""YouTube tools with LangChain decorators."""

import re
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import settings


_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

# Your channel info
CHANNEL_URL = settings.youtube_channel_url or "https://www.youtube.com/@boldinagy"
CHANNEL_HANDLE = "@boldinagy"


# --- Pydantic Schemas ---


class YouTubeVideoInput(BaseModel):
    """Input for loading a YouTube video."""

    url: str = Field(description="YouTube video URL or video ID")


class YouTubeSearchInput(BaseModel):
    """Input for searching YouTube."""

    query: str = Field(description="Search query for YouTube videos")


# --- Helper Functions ---


def extract_video_id(url: str) -> str:
    """Extract video ID from URL."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url


def load_youtube(url: str, languages: list[str] = None) -> list[Document]:
    """Load transcript from YouTube video."""
    video_id = extract_video_id(url)
    languages = languages or ["en", "hu"]

    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=languages)
        full_text = " ".join(entry.text for entry in transcript)
    except Exception:
        return []

    doc = Document(
        page_content=full_text,
        metadata={"source": f"youtube:{video_id}", "type": "video"},
    )
    return _splitter.split_documents([doc])


# --- Tool Functions ---


@tool(args_schema=YouTubeVideoInput)
def load_youtube_transcript(url: str) -> str:
    """Load transcript from a YouTube video. Use when user provides a YouTube link or asks about video content."""
    docs = load_youtube(url)
    if not docs:
        return f"Could not load transcript from {url}. The video may not have captions."

    # Combine chunks (limit to avoid context overflow)
    content = "\n\n".join(d.page_content for d in docs[:3])
    return f"YouTube transcript (first 3 chunks):\n{content}"


@tool
def get_coach_channel_info() -> str:
    """Get information about the coach's YouTube channel. Use when user asks about Boldi's videos or channel."""
    return f"""Coach's YouTube Channel:
- Handle: {CHANNEL_HANDLE}
- URL: {CHANNEL_URL}
- Content: Powerlifting technique tutorials, competition prep, training philosophy

Note: To get specific video content, ask the user for a video URL as I cannot search the channel directly without API keys."""


@tool(args_schema=YouTubeSearchInput)
def suggest_youtube_search(query: str) -> str:
    """Suggest a YouTube search for powerlifting content. Use when user needs video resources."""
    search_url = (
        f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    )
    coach_search = f"https://www.youtube.com/{CHANNEL_HANDLE}/search?query={query.replace(' ', '+')}"

    return f"""YouTube Search Suggestions:
1. Search coach's channel: {coach_search}
2. General YouTube search: {search_url}

Tip: Check {CHANNEL_HANDLE} first for specific powerlifting technique guidance."""


# Export all tools
ALL_TOOLS = [load_youtube_transcript, get_coach_channel_info, suggest_youtube_search]
