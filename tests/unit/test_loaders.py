"""
Unit tests for the RAG loaders.

Tests document loading and chunking for PDFs, Markdown, and YouTube.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.rag.loaders.markdown_loader import MarkdownLoader
from src.rag.loaders.pdf_loader import PDFLoader
from src.rag.loaders.youtube_loader import YouTubeLoader


class TestPDFLoader:
    """Tests for PDF document loader."""

    def test_pdf_loader_initialization(self):
        """Test PDF loader creates with default settings."""
        loader = PDFLoader()
        assert loader._chunk_size == 1000
        assert loader._chunk_overlap == 200

    def test_pdf_loader_custom_settings(self):
        """Test PDF loader with custom chunk settings."""
        loader = PDFLoader(chunk_size=500, chunk_overlap=50)
        assert loader._chunk_size == 500
        assert loader._chunk_overlap == 50

    def test_pdf_loader_file_not_found(self):
        """Test error handling for missing file."""
        loader = PDFLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_file("nonexistent.pdf")

    def test_pdf_loader_directory_not_found(self):
        """Test error handling for missing directory."""
        loader = PDFLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_directory("nonexistent_dir")

    def test_pdf_get_file_count(self, tmp_path):
        """Test counting PDF files in directory."""
        # Create temp PDF files (empty)
        (tmp_path / "file1.pdf").touch()
        (tmp_path / "file2.pdf").touch()
        (tmp_path / "file3.txt").touch()  # Not a PDF

        loader = PDFLoader()
        count = loader.get_file_count(tmp_path)
        assert count == 2


class TestMarkdownLoader:
    """Tests for Markdown document loader."""

    def test_markdown_loader_initialization(self):
        """Test Markdown loader creates with default settings."""
        loader = MarkdownLoader()
        assert loader._chunk_size == 800
        assert loader._chunk_overlap == 100

    def test_markdown_loader_load_file(self, tmp_path):
        """Test loading a markdown file."""
        # Create test markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Heading\n\nThis is test content.")

        loader = MarkdownLoader()
        docs = loader.load_file(md_file)

        assert len(docs) >= 1
        assert (
            "test" in docs[0].page_content.lower()
            or "heading" in docs[0].page_content.lower()
        )
        assert docs[0].metadata["source_type"] == "markdown"
        assert docs[0].metadata["topic"] == "test"

    def test_markdown_loader_extracts_topic_from_filename(self, tmp_path):
        """Test that topic is extracted from filename."""
        md_file = tmp_path / "squat.md"
        md_file.write_text("Squat content here")

        loader = MarkdownLoader()
        docs = loader.load_file(md_file)

        assert docs[0].metadata["topic"] == "squat"

    def test_markdown_loader_file_not_found(self):
        """Test error handling for missing file."""
        loader = MarkdownLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_file("nonexistent.md")

    def test_markdown_loader_directory(self, tmp_path):
        """Test loading multiple files from directory."""
        (tmp_path / "file1.md").write_text("Content 1")
        (tmp_path / "file2.md").write_text("Content 2")
        (tmp_path / ".gitkeep").write_text("")  # Should be skipped

        loader = MarkdownLoader()
        docs = loader.load_directory(tmp_path)

        # Should have docs from both files (gitkeep skipped)
        sources = set(d.metadata["filename"] for d in docs)
        assert "file1.md" in sources
        assert "file2.md" in sources
        assert ".gitkeep" not in sources

    def test_markdown_get_file_count(self, tmp_path):
        """Test counting markdown files in directory."""
        (tmp_path / "file1.md").touch()
        (tmp_path / "file2.md").touch()
        (tmp_path / ".hidden.md").touch()  # Hidden, should be excluded

        loader = MarkdownLoader()
        count = loader.get_file_count(tmp_path)
        assert count == 2


class TestYouTubeLoader:
    """Tests for YouTube transcript loader."""

    def test_youtube_loader_initialization(self):
        """Test YouTube loader creates with default settings."""
        loader = YouTubeLoader()
        assert loader._chunk_size == 800
        assert "en" in loader._languages

    def test_extract_video_id_from_watch_url(self):
        """Test extracting video ID from standard watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = YouTubeLoader.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_from_short_url(self):
        """Test extracting video ID from short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = YouTubeLoader.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_from_embed_url(self):
        """Test extracting video ID from embed URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = YouTubeLoader.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_already_id(self):
        """Test that raw video ID is returned as-is."""
        video_id = "dQw4w9WgXcQ"
        result = YouTubeLoader.extract_video_id(video_id)
        assert result == video_id

    def test_extract_video_id_with_params(self):
        """Test extracting video ID from URL with extra params."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        video_id = YouTubeLoader.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    @patch("src.rag.loaders.youtube_loader.YouTubeTranscriptApi")
    def test_load_video_with_mock(self, mock_api):
        """Test loading video with mocked API."""
        # Mock the transcript API
        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [
            {"text": "Hello world"},
            {"text": "This is a test transcript"},
        ]

        mock_list = MagicMock()
        mock_list.find_transcript.return_value = mock_transcript
        mock_api.list_transcripts.return_value = mock_list

        loader = YouTubeLoader()
        docs = loader.load_video("test_video_id", title="Test Video")

        assert len(docs) >= 1
        assert docs[0].metadata["source_type"] == "youtube"
        assert docs[0].metadata["video_id"] == "test_video_id"


class TestLoadersIntegration:
    """Integration tests for loaders with real data directory."""

    def test_load_real_markdown_notes(self):
        """Test loading actual coaching notes if they exist."""
        notes_dir = Path("data/notes")

        if not notes_dir.exists():
            pytest.skip("Notes directory not found")

        loader = MarkdownLoader()
        count = loader.get_file_count(notes_dir)

        if count == 0:
            pytest.skip("No markdown files found")

        docs = loader.load_directory(notes_dir)

        assert len(docs) > 0
        # Should have topic metadata
        topics = set(d.metadata.get("topic") for d in docs)
        assert len(topics) > 0

    def test_load_real_pdf_rules(self):
        """Test loading actual PDF rules if they exist."""
        rules_dir = Path("data/rules")

        if not rules_dir.exists():
            pytest.skip("Rules directory not found")

        loader = PDFLoader()
        count = loader.get_file_count(rules_dir)

        if count == 0:
            pytest.skip("No PDF files found")

        # Just test first file to avoid long load times
        pdf_files = list(rules_dir.glob("*.pdf"))
        if pdf_files:
            docs = loader.load_file(pdf_files[0])
            assert len(docs) > 0
            assert docs[0].metadata["source_type"] == "pdf"
