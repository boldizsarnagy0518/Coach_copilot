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

# Lazy-initialized YouTube API client
_youtube_api = None


def _get_youtube_api():
    """Get or create YouTube Data API client."""
    global _youtube_api

    if _youtube_api is not None:
        return _youtube_api

    if not settings.youtube_api_key:
        return None

    try:
        from googleapiclient.discovery import build

        _youtube_api = build("youtube", "v3", developerKey=settings.youtube_api_key)
        return _youtube_api
    except Exception as e:
        print(f"Failed to initialize YouTube API: {e}")
        return None


class YouTubeVideoInput(BaseModel):
    """Input for loading a YouTube video."""

    url: str = Field(description="YouTube video URL or video ID")


class YouTubeSearchInput(BaseModel):
    """Input for searching YouTube."""

    query: str = Field(description="Search query for YouTube videos")


class VideoIdInput(BaseModel):
    """Input for getting video details."""

    video_id: str = Field(description="YouTube video ID (11 characters)")


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
    api = _get_youtube_api()

    if api and settings.youtube_channel_id:
        try:
            response = (
                api.channels()
                .list(part="snippet,statistics", id=settings.youtube_channel_id)
                .execute()
            )

            if response.get("items"):
                channel = response["items"][0]
                snippet = channel.get("snippet", {})
                stats = channel.get("statistics", {})

                return f"""Coach's YouTube Channel:
- Name: {snippet.get("title", CHANNEL_HANDLE)}
- Handle: {CHANNEL_HANDLE}
- URL: {CHANNEL_URL}
- Subscribers: {stats.get("subscriberCount", "N/A")}
- Total Videos: {stats.get("videoCount", "N/A")}
- Total Views: {stats.get("viewCount", "N/A")}
- Description: {snippet.get("description", "Powerlifting content")[:200]}...

Use `search_channel_videos` to find specific videos."""
        except Exception as e:
            print(f"YouTube API error: {e}")

    # Fallback without API
    return f"""Coach's YouTube Channel:
- Handle: {CHANNEL_HANDLE}
- URL: {CHANNEL_URL}
- Content: Powerlifting technique tutorials, competition prep, training philosophy

Note: Set YOUTUBE_API_KEY in .env to enable video search and detailed stats."""


@tool(args_schema=YouTubeSearchInput)
def search_channel_videos(query: str) -> str:
    """Search for videos on the coach's YouTube channel. Use when user wants to find specific videos about a topic. Costs 100 API quota units."""
    api = _get_youtube_api()

    if not api:
        # Fallback: provide search URL
        search_url = f"https://www.youtube.com/{CHANNEL_HANDLE}/search?query={query.replace(' ', '+')}"
        return f"""YouTube API not configured. Search manually:
{search_url}

To enable API search, add YOUTUBE_API_KEY and YOUTUBE_CHANNEL_ID to .env"""

    try:
        response = (
            api.search()
            .list(
                part="snippet",
                channelId=settings.youtube_channel_id,
                q=query,
                type="video",
                maxResults=5,
                order="relevance",
            )
            .execute()
        )

        if not response.get("items"):
            return f"No videos found for '{query}' on {CHANNEL_HANDLE}"

        results = []
        for item in response["items"]:
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            results.append(f"""
- **{snippet.get("title", "Untitled")}**
  URL: https://youtu.be/{video_id}
  Published: {snippet.get("publishedAt", "N/A")[:10]}
  {snippet.get("description", "")[:100]}...""")

        return f"Found {len(results)} videos for '{query}':\n" + "\n".join(results)

    except Exception as e:
        return f"Error searching videos: {e}"


@tool(args_schema=VideoIdInput)
def get_video_details(video_id: str) -> str:
    """Get detailed information about a YouTube video. Costs 1 API quota unit."""
    api = _get_youtube_api()

    if not api:
        return f"YouTube API not configured. View video at: https://youtu.be/{video_id}"

    try:
        response = (
            api.videos()
            .list(part="snippet,statistics,contentDetails", id=video_id)
            .execute()
        )

        if not response.get("items"):
            return f"Video not found: {video_id}"

        video = response["items"][0]
        snippet = video.get("snippet", {})
        stats = video.get("statistics", {})
        content = video.get("contentDetails", {})

        # Parse duration (ISO 8601 format)
        duration = content.get("duration", "PT0S")
        duration = (
            duration.replace("PT", "")
            .replace("H", "h ")
            .replace("M", "m ")
            .replace("S", "s")
        )

        return f"""**{snippet.get("title", "Untitled")}**

- URL: https://youtu.be/{video_id}
- Channel: {snippet.get("channelTitle", "Unknown")}
- Published: {snippet.get("publishedAt", "N/A")[:10]}
- Duration: {duration}
- Views: {stats.get("viewCount", "N/A")}
- Likes: {stats.get("likeCount", "N/A")}
- Comments: {stats.get("commentCount", "N/A")}

**Description:**
{snippet.get("description", "No description")[:500]}"""

    except Exception as e:
        return f"Error getting video details: {e}"


@tool
def list_channel_playlists() -> str:
    """List all playlists on the coach's YouTube channel. Costs 1 API quota unit."""
    api = _get_youtube_api()

    if not api:
        return f"YouTube API not configured. View playlists at: {CHANNEL_URL}/playlists"

    if not settings.youtube_channel_id:
        return "YOUTUBE_CHANNEL_ID not set in .env"

    try:
        response = (
            api.playlists()
            .list(
                part="snippet,contentDetails",
                channelId=settings.youtube_channel_id,
                maxResults=10,
            )
            .execute()
        )

        if not response.get("items"):
            return "No playlists found on channel"

        results = []
        for item in response["items"]:
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            playlist_id = item.get("id", "")

            results.append(f"""
- **{snippet.get("title", "Untitled")}**
  Videos: {content.get("itemCount", 0)}
  URL: https://youtube.com/playlist?list={playlist_id}""")

        return f"Found {len(results)} playlists:\n" + "\n".join(results)

    except Exception as e:
        return f"Error listing playlists: {e}"


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


ALL_TOOLS = [
    load_youtube_transcript,
    get_coach_channel_info,
    search_channel_videos,
    get_video_details,
    list_channel_playlists,
    suggest_youtube_search,
]
