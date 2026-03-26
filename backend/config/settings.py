"""
Application settings management using Pydantic Settings.
Loads configuration from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Finnhub (News)
    finnhub_api_key: Optional[str] = None
    adanos_api_key: Optional[str] = None
    adanos_base_url: str = "https://api.adanos.org"
    adanos_timeout_seconds: float = 4.0

    # Qdrant (Vector Store)
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "investment_docs"
    qdrant_api_key: Optional[str] = None

    # FinBERT (Local Models)
    finbert_model_name: str = "ProsusAI/finbert"
    finbert_embedding_model: str = "ProsusAI/finbert"
    finbert_device: str = "cpu"

    # SEC EDGAR
    sec_edgar_user_agent: str = "InvestmentResearch research@example.com"

    # Agent Timeouts (seconds)
    agent_timeout_technical: int = 30
    agent_timeout_sentiment: int = 20
    agent_timeout_fundamental: int = 60

    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
