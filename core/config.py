"""
Configuration Module.

Loads environment variables from .env file and exposes structured config variables
using pydantic-settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure environment variables are loaded from file system first
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings(BaseSettings):
    """Pipeline-wide configuration variables validated via pydantic-settings."""

    # Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parents[1]
    DATA_DIR: Path = Field(default=Path("data"))
    OUTPUT_DIR: Path = Field(default=Path("output"))
    REPORTS_DIR: Path = Field(default=Path("reports"))
    LOGS_DIR: Path = Field(default=Path("logs"))
    TEMPLATES_DIR: Path = Field(default=Path("templates"))

    # Environment
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    # API Keys
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    TAVILY_API_KEY: Optional[str] = Field(default=None)
    SERPER_API_KEY: Optional[str] = Field(default=None)

    # Concurrency and Safety Limits
    MAX_CONCURRENT_RESEARCHERS: int = Field(default=1, ge=1)
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30, ge=1)
    HTTP_MAX_RETRIES: int = Field(default=3, ge=0)
    HTTP_RETRY_BACKOFF_FACTOR: float = Field(default=2.0, ge=1.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        # Convert relative paths to absolute paths relative to BASE_DIR if needed
        dirs = [
            self.BASE_DIR / self.DATA_DIR,
            self.BASE_DIR / self.DATA_DIR / "raw",
            self.BASE_DIR / self.DATA_DIR / "processed",
            self.BASE_DIR / self.DATA_DIR / "verified",
            self.BASE_DIR / self.OUTPUT_DIR,
            self.BASE_DIR / self.REPORTS_DIR,
            self.BASE_DIR / self.LOGS_DIR,
            self.BASE_DIR / self.TEMPLATES_DIR
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# Export a singleton instance of settings
settings = Settings()
# Ensure directories are created on config load
settings.ensure_directories()
