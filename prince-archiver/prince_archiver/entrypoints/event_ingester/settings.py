from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SRC_DIR: Path
    SRC_LIFESPAN: timedelta = timedelta(hours=8)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
