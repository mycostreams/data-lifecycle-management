from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    REDIS_DSN: RedisDsn

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
