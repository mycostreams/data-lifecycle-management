from dataclasses import dataclass

from aio_pika import ExchangeType
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONNECTION_URL = "amqp://guest:guest@localhost/"


def get_connection_url(connection_url: str | None):
    if connection_url:
        return connection_url

    settings = BrokerSettings()
    return settings.CONNECTION_URL


class BrokerSettings(BaseSettings):

    CONNECTION_URL: str = DEFAULT_CONNECTION_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):

    USERNAME: str
    PASSWORD: str
    HOST: str = "snellius.surf.nl"
    PORT: int = 22

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@dataclass(kw_only=True)
class ExchangeConfig:
    """Exchange config for RabbitMQ"""

    name: str = "slurm-uploader"
    type: ExchangeType = ExchangeType.FANOUT
    routing_key: str = "slurm-uploader"
