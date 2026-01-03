"""Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production"] = "development"

    llm_provider: Literal["ollama", "gemini"] = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_fast_model: str = "qwen2.5:0.5b"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3-flash-preview"
    gemini_fast_model: str = "gemini-2.5-flash"

    embedding_provider: Literal["ollama", "gemini"] = "ollama"
    ollama_embedding_model: str = "nomic-embed-text"
    gemini_embedding_model: str = "models/text-embedding-004"

    chroma_persist_directory: Path = Path("./data/chroma_db")
    duckdb_path: Path = Path("./data/athlete_data.duckdb")

    google_sheets_credentials_path: Path = Path("secrets/credentials.json")
    google_sheets_spreadsheet_id: str | None = None

    athlete_pins: str = "{}"

    youtube_channel_url: str = "https://www.youtube.com/@boldinagy"
    youtube_api_key: str | None = None
    youtube_channel_id: str | None = (
        None  # e.g., "UCxxxxxxxx" - can be found in channel URL
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
