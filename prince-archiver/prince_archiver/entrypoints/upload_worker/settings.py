from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from prince_archiver.config import AWSSettings


class Settings(AWSSettings, BaseSettings):
    PRINCE_SRC_DIR: Path
    STAGING_DIR: Path | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
