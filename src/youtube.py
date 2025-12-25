"""YouTube transcript loader."""

import re
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

CHANNEL_URL = "https://www.youtube.com/@boldinagy"


def extract_video_id(url: str) -> str:
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
