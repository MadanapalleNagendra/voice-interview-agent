"""
app/core/config.py
Central configuration — all settings read from environment variables.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── API Keys ───────────────────────────────────────────────────────────
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""

    # ── OpenAI ────────────────────────────────────────────────────────────
    openai_chat_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_whisper_model: str = "whisper-1"

    # ── ElevenLabs ────────────────────────────────────────────────────────
    elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # "Bella" — natural female voice
    elevenlabs_model_id: str = "eleven_multilingual_v2"

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/interview_db"

    # ── Redis ─────────────────────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"
    redis_cache_ttl: int = 3600  # seconds

    # ── FAISS ─────────────────────────────────────────────────────────────
    faiss_index_path: str = "data/faiss_index"
    qa_dataset_path: str = "data/qa_dataset.json"
    retrieval_top_k: int = 3

    # ── Interview ─────────────────────────────────────────────────────────
    max_questions: int = 10
    supported_languages: list[str] = ["en", "hi", "de"]
    default_language: str = "en"

    # ── Celery ────────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # ── FastAPI ───────────────────────────────────────────────────────────
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
