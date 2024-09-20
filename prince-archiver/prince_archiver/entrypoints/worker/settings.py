from pydantic import HttpUrl, PostgresDsn

from prince_archiver.config import AWSSettings, CommonSettings


class Settings(AWSSettings, CommonSettings):
    POSTGRES_DSN: PostgresDsn
    RABBITMQ_DSN: str

    SURF_USERNAME: str
    SURF_PASSWORD: str

    DATA_ARCHIVE_HOST: str = "archive.surfsara.nl"

    WEBHOOK_URL: HttpUrl | None = None

    ARCHIVE_TRANSITION_DAYS: int = 2
