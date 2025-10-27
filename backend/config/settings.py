"""
Application settings management using Pydantic Settings.
Loads configuration from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""

    # MongoDB Configuration (Free M0 tier)
    mongodb_uri: str
    mongodb_db_name: str = "investment_research"

    # ChromaDB Configuration (local vector database)
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "investment_docs"

    # API Keys
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    news_api_key: Optional[str] = None
    yahoo_finance_api_key: Optional[str] = None

    # SEC EDGAR Configuration
    sec_edgar_user_agent: str

    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Session Management
    session_expire_minutes: int = 30
    session_secret_key: str

    # WebSocket Settings
    ws_heartbeat_interval: int = 30

    # Alert System
    alert_check_interval: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
