"""
Central configuration for AlphaFlow AI.
Values are read from environment variables / .env, with safe
defaults so the system runs out-of-the-box with zero API keys
(the Data Collection layer uses yfinance, which is free and keyless).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./alphaflow.db"
    redis_url: str = "redis://localhost:6379/0"

    newsapi_key: str = ""
    fii_dii_api_key: str = ""

    # Weights used by the Feature Engineering + Prediction layer.
    # Centralized so they can be tuned without touching agent cod.
    technical_weight: float = 0.30
    fundamental_weight: float = 0.25
    sentiment_weight: float = 0.20
    momentum_weight: float = 0.15
    event_weight: float = 0.10

    # Cache TTL (seconds) for expensive market data calls.
    cache_ttl_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
