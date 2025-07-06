"""Configuration settings for the application."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    app_name: str = "Equal-Weighted Stock Index Tracker"
    api_version: str = "v1"
    debug: bool = True
    
    # Database Settings
    database_path: str = "data/hedgineer.db"
    
    # Redis Settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_ttl: int = 3600  # 1 hour default cache TTL
    
    # Data Source Settings
    data_source: str = "yfinance"  # Options: yfinance, alphavantage
    alphavantage_api_key: Optional[str] = None
    
    # Index Settings
    index_size: int = 10  # Top 10 stocks by market cap
    min_trading_days: int = 30  # Minimum trading days of history
    
    # Export Settings
    export_dir: str = "exports"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Clear the cache to ensure new settings are loaded
get_settings.cache_clear()