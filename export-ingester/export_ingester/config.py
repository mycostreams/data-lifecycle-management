from datetime import timedelta
from pathlib import Path

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SFTP_USERNAME: str
    SFTP_PASSWORD: str
    SFTP_HOST: str

    BASE_URL: HttpUrl
    SBATCH_COMMAND: str
    SBATCH_VIDEO_COMMAND: str = "sbatch /home/svstaalduine/orchestrator/orchestrator/bash_scripts/daily_videos.sh /scratch-shared/amftrack_prod/daily_video"
    TIME_RANGE: timedelta = timedelta(days=4)
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
