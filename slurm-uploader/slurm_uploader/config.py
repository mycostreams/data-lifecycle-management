from dataclasses import dataclass

from aio_pika import ExchangeType
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONNECTION_URL = "amqp://guest:guest@localhost/"


class Settings(BaseSettings):

    CONNECTION_URL: str = DEFAULT_CONNECTION_URL

    USERNAME: str
    PASSWORD: str
    HOST: str = "snellius.surf.nl"
    PORT: int = 22

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@dataclass(kw_only=True)
class ExchangeConfig:
    """Exchange config for RabbitMQ"""

    name: str = "slurm-uploader"
    type: ExchangeType = ExchangeType.FANOUT
    routing_key: str = "slurm-uploader"
