import os
from functools import lru_cache
from pathlib import Path

import sentry_sdk
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    enable_tracing=True,
)


class CommonSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class WatcherSettings(CommonSettings):

    REDIS_DSN: RedisDsn
    POSTGRES_DSN: PostgresDsn

    DATA_DIR: Path

    WATCHFILES_FORCE_POLLING: bool | None = None


class WorkerSettings(CommonSettings):

    REDIS_DSN: RedisDsn
    POSTGRES_DSN: PostgresDsn

    DATA_DIR: Path

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_ENDPOINT_URL: str | None = None
    AWS_REGION_NAME: str | None = None

    UPLOAD_MAX_CONCURRENCY: int = 5


class ArchiveWorkerSettings(CommonSettings):

    REDIS_DSN: RedisDsn
    AWS_BUCKET_NAME: str

    SURF_USERNAME: str
    SURF_PASSWORD: str


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
