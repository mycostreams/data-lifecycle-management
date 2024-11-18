import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Awaitable, Callable

from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractRobustExchange,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class ExchangeConfig:
    name: str = "surf-data-archive"
    type: ExchangeType = ExchangeType.FANOUT


@dataclass
class QueueConfig:
    name: str | None = "state-manager"
    durable: bool = True


class ManagedSubscriber:
    def __init__(
        self,
        connection_url: str,
        message_handler: Callable[[AbstractIncomingMessage], Awaitable[None]],
        exchange_config: ExchangeConfig | None = None,
        queue_config: QueueConfig | None = None,
    ):
        self.connection_url = connection_url
        self.exchange_config = exchange_config or ExchangeConfig()
        self.queue_config = queue_config or QueueConfig()

        self.message_handler = message_handler

        self.exit_stack: AsyncExitStack | None = None

        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractRobustChannel | None = None
        self.exchange: AbstractRobustExchange | None
        self.queue: AbstractQueue | None = None

    async def __aenter__(self):
        self.exit_stack = await AsyncExitStack().__aenter__()

        self.connection = await connect_robust(self.connection_url)
        await self.exit_stack.enter_async_context(self.connection)

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        self.exchange = await self.channel.declare_exchange(
            self.exchange_config.name,
            self.exchange_config.type,
        )

        self.queue = await self.channel.declare_queue(
            self.queue_config.name,
            durable=self.queue_config.durable,
        )

        await self.queue.bind(self.exchange)
        await self.queue.consume(self.message_handler)

        LOGGER.info("Consuming `%s`", self.exchange_config.name)

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if self.exit_stack:
            await self.exit_stack.aclose()
