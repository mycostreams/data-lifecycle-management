from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic

from aio_pika import DeliveryMode, ExchangeType, Message, connect
from aio_pika.abc import AbstractConnection, AbstractExchange
from pydantic import BaseModel

from .abc import AbstractConfig, ConfigT


class BaseMessage(BaseModel):
    pass


class AbstractPublisher(ABC):
    @abstractmethod
    async def publish(self, message: BaseMessage): ...


class AbstractManagedPublisher(Generic[ConfigT], ABC):
    def __init__(self, config: ConfigT):
        self.config = config

    @abstractmethod
    async def __aenter__(self) -> AbstractPublisher: ...

    @abstractmethod
    async def __aexit__(self, *args) -> None: ...


class _Publisher(AbstractPublisher):
    def __init__(
        self,
        exchange: AbstractExchange,
        routing_key: str,
        delivery_mode: DeliveryMode = DeliveryMode.PERSISTENT,
    ):
        self.exchange = exchange
        self.routing_key = routing_key
        self.delivery_mode = delivery_mode

    async def publish(self, message: BaseMessage):
        _message = Message(
            message.model_dump_json(indent=4).encode(),
            delivery_mode=self.delivery_mode,
        )
        await self.exchange.publish(_message, self.routing_key)


@dataclass
class PublisherConfig(AbstractConfig):
    connection_url: str

    exchange_name: str = "surf-data-archive"
    exchange_type: ExchangeType = ExchangeType.FANOUT
    routing_key: str = "archiving-cron"


class ManagedPublisher(AbstractManagedPublisher[PublisherConfig]):
    conn: AbstractConnection

    async def __aenter__(self) -> _Publisher:
        self.conn = await connect(self.config.connection_url)
        await self.conn.__aenter__()

        channel = await self.conn.channel()

        exchange = await channel.declare_exchange(
            self.config.exchange_name,
            self.config.exchange_type,
        )

        return _Publisher(
            exchange=exchange,
            routing_key=self.config.routing_key,
        )

    async def __aexit__(self, *_):
        await self.conn.__aexit__(None, None, None)
