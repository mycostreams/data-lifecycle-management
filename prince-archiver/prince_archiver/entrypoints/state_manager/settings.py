from pydantic import HttpUrl, PostgresDsn

from prince_archiver.config import CommonSettings


class Settings(CommonSettings):
    POSTGRES_DSN: PostgresDsn
    RABBITMQ_DSN: str

    WEBHOOK_URL: HttpUrl | None = None
