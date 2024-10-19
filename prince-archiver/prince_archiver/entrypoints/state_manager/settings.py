from pydantic import PostgresDsn

from prince_archiver.config import CommonSettings


class Settings(CommonSettings):
    POSTGRES_DSN: PostgresDsn
    RABBITMQ_DSN: str
