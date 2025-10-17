"""Configuration management with environment-based settings."""

import os
from typing import Optional
from enum import Enum
from pydantic_settings import BaseSettings
from pydantic import Field


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with validation."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # Database
    default_mysql_port: int = Field(default=3306)
    max_query_execution_time: int = Field(default=30)
    enable_query_logging: bool = Field(default=True)

    # Connection Pool
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=10)
    db_pool_recycle: int = Field(default=3600)

    # AI Model
    default_model: str = Field(default="gemini-2.0-flash-exp")
    ai_max_tokens: int = Field(default=2048)
    ai_temperature: float = Field(default=0.7)

    # Session
    max_chat_history: int = Field(default=50)
    session_timeout_minutes: int = Field(default=60)

    # Security
    admin_token: str = Field(default="secure-admin-token", env="ADMIN_TOKEN")

    # Directories
    backup_output_dir: str = Field(default="db_backups")
    logs_dir: str = Field(default="logs")
    exports_dir: str = Field(default="exports")

    # CORS
    cors_origins: list[str] = Field(default=["*"])

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
