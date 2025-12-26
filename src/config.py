"""Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production"] = "development"

    # LLM
    llm_provider: Literal["ollama", "gemini"] = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_fast_model: str = "qwen2.5:0.5b"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3-flash-preview"
    gemini_fast_model: str = "gemini-2.5-flash"

    # Embeddings
    embedding_provider: Literal["ollama", "gemini"] = "ollama"
    ollama_embedding_model: str = "nomic-embed-text"
    gemini_embedding_model: str = "models/text-embedding-004"

    # Data
    chroma_persist_directory: Path = Path("./data/chroma_db")

    # Google Sheets
    google_sheets_credentials_path: str | None = "secrets/credentials.json"
    google_sheets_spreadsheet_id: str | None = None

    @property
    def credentials_path(self) -> Path:
        """Resolve absolute path to credentials."""
        if not self.google_sheets_credentials_path:
            return Path("secrets/credentials.json")

        # Try finding it relative to current working directory first
        cwd_path = Path.cwd() / self.google_sheets_credentials_path
        if cwd_path.exists():
            return cwd_path
        # Fallback to absolute path provided
        return Path(self.google_sheets_credentials_path)

    # Athlete PINs (JSON format: {"Boldi": "1234", "John": "5678"})
    athlete_pins: str = "{}"

    # YouTube
    youtube_channel_url: str = "https://www.youtube.com/@boldinagy"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
