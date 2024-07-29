import os
from functools import lru_cache
from pathlib import Path

import sentry_sdk
from pydantic import Field, HttpUrl, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    enable_tracing=True,
)


class _SentinelPath(Path):
    """Sentinel value for `pathlib.Path` objects."""


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

    AWS_BUCKET_NAME: str

    UPLOAD_MAX_CONCURRENCY: int = 5


class WatcherSettings(CommonSettings):
    DATA_DIR: Path

    EVENTS_DIR: Path = Field(default_factory=_SentinelPath)

    WATCHFILES_FORCE_POLLING: bool | None = None

    @model_validator(mode="after")
    def set_events_dir(self) -> "WatcherSettings":
        if isinstance(self.EVENTS_DIR, _SentinelPath):
            self.EVENTS_DIR = self.DATA_DIR / "events"
        return self


class WorkerSettings(AWSSettings, CommonSettings):
    DATA_DIR: Path


class ArchiveWorkerSettings(AWSSettings, CommonSettings):
    RABBITMQ_DSN: str

    SURF_USERNAME: str
    SURF_PASSWORD: str

    DATA_ARCHIVE_HOST: str = "archive.surfsara.nl"

    WEBHOOK_URL: HttpUrl | None = None

    ARCHIVE_TRANSITION_DAYS: int = 2


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
