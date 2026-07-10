"""Application configuration with pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "Interview AI"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "change-me-in-production"
    allowed_hosts: list[str] = ["*"]

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/interview_ai"
    sync_database_url: str = "postgresql://postgres:postgres@localhost:5432/interview_ai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Vector DB
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "interview-ai-jobs"

    # Object Storage
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "interview-ai"
    s3_region: str = "us-east-1"
    use_minio: bool = True

    # AI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    whisper_model: str = "base"
    spacy_model: str = "en_core_web_md"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"

    # Auth
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Security
    rate_limit_per_minute: int = 60
    max_upload_size_mb: int = 10
    password_min_length: int = 8

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    default_from_email: str = "noreply@interview-ai.example.com"

    # Frontend
    frontend_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
