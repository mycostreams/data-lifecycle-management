from datetime import timedelta
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from prince_archiver.definitions import System


class Settings(BaseSettings):
    SRC_DIR: Path
    SRC_LIFESPAN: timedelta = timedelta(hours=8)
    SRC_SYSTEMS_DELETE: set[System] = Field(default_factory=set)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
