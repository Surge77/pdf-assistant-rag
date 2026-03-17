from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PDF Assistant RAG"
    api_prefix: str = "/api"
    data_dir: Path = Path("backend/data")
    upload_dir: Path = Path("backend/data/uploads")
    chroma_dir: Path = Path("backend/data/chroma")
    documents_dir: Path = Path("backend/data/documents")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:latest"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
