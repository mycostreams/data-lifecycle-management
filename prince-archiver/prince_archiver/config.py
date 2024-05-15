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
    POSTGRES_DSN: PostgresDsn

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AWSSettings(BaseSettings):

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_ENDPOINT_URL: str | None = None
    AWS_REGION_NAME: str | None = None

    UPLOAD_MAX_CONCURRENCY: int = 5


class WatcherSettings(CommonSettings):

    DATA_DIR: Path

    WATCHFILES_FORCE_POLLING: bool | None = None


class WorkerSettings(AWSSettings, CommonSettings):

    DATA_DIR: Path

    AWS_BUCKET_NAME: str


class ArchiveWorkerSettings(AWSSettings, CommonSettings):

    SURF_USERNAME: str
    SURF_PASSWORD: str

    DATA_ARCHIVE_HOST: str = "archive.surfsara.nl"

    UPLOAD_EXPIRY_DAYS: int = 5


class SubscriberSettings(BaseSettings):

    POSTGRES_DSN: PostgresDsn
    RABBITMQ_DSN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
