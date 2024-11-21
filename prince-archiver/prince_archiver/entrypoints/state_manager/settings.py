from pydantic import PostgresDsn
from pydantic_settings import SettingsConfigDict

from prince_archiver.config import AWSSettings, CommonSettings


class Settings(AWSSettings, CommonSettings):
    POSTGRES_DSN: PostgresDsn
    RABBITMQ_DSN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
