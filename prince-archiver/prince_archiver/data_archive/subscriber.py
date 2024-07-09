import asyncio
import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Awaitable, Callable

from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage

from prince_archiver.config import SubscriberSettings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.logging import configure_logging
from prince_archiver.messagebus import MessageBus

from .dto import UpdateArchiveEntries
from .handlers import SubscriberMessageHandler, add_data_archive_entries

LOGGER = logging.getLogger(__name__)


@dataclass
class ExchangeConfig:
    name: str = "surf-data-archive"
    type: ExchangeType = ExchangeType.FANOUT


class ManagedSubscriber:
    def __init__(
        self,
        connection_url: str,
        message_handler: Callable[[AbstractIncomingMessage], Awaitable[None]],
        exchange_config: ExchangeConfig | None = None,
    ):
        self.connection_url = connection_url
        self.exchange_config = exchange_config or ExchangeConfig()
        self.message_handler = message_handler

        self.exit_stack: AsyncExitStack | None = None

    async def __aenter__(self):
        self.exit_stack = await AsyncExitStack().__aenter__()

        connection = await connect_robust(self.connection_url)
        await self.exit_stack.enter_async_context(connection)

        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            self.exchange_config.name,
            self.exchange_config.type,
        )

        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange)
        await queue.consume(self.message_handler)

        return self

    async def __aexit__(self, *_):
        if self.exit_stack:
            await self.exit_stack.aclose()


async def main(*, _settings: SubscriberSettings | None = None):
    configure_logging()

    settings = _settings or SubscriberSettings()

    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))

    def _messagebus_factory() -> MessageBus:
        return MessageBus(
            handlers={UpdateArchiveEntries: [add_data_archive_entries]},
            uow=UnitOfWork(sessionmaker),
        )

    subscriber = ManagedSubscriber(
        connection_url=settings.RABBITMQ_DSN,
        message_handler=SubscriberMessageHandler(_messagebus_factory),
    )
    async with subscriber:
        logging.info("Starting up")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
