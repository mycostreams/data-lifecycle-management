from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PRINCE_SRC_DIR: Path
    STAGING_DIR: Path | None = None

    WATCHFILES_FORCE_POLLING: bool = True
    SRC_LIFESPAN: timedelta = timedelta(hours=8)
    STAGING_LIFESPAN: timedelta = timedelta(days=24)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
