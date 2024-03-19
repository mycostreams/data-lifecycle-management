from functools import lru_cache
from pathlib import Path

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    POSTGRES_DSN: PostgresDsn

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_ENDPOINT_URL: str | None = None

    DATA_DIR: Path
    ARCHIVE_DIR: Path
    TEMP_FILE_DIR: Path

    CELERY_BROKER_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
