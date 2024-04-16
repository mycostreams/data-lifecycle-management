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

    REDIS_DSN: RedisDsn

    DATA_DIR: Path

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class WatcherSettings(CommonSettings):

    POSTGRES_DSN: PostgresDsn


class WorkerSettings(CommonSettings):

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_ENDPOINT_URL: str | None = None
    AWS_REGION_NAME: str | None = None


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
