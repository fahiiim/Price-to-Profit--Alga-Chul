"""Typed application settings loaded once from the environment."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration. Every value can be overridden with `PTP_<NAME>`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PTP_",
        extra="ignore",
    )

    app_name: str = "Price to Profit API"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'price_to_profit.db'}"
    media_dir: Path = PROJECT_ROOT / "media"
    max_logo_bytes: int = 2_000_000
    cors_origins: list[str] = ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
