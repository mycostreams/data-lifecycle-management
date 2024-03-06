import asyncio
import logging

from aio_pika import connect
from aio_pika.abc import AbstractIncomingMessage

from .config import ExchangeConfig

LOGGER = logging.getLogger(__name__)


async def on_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        print(f"[x] {message.body!r}")


async def subscriber(
    connection_url: str,
    *,
    exchange_config: ExchangeConfig | None = None,
) -> None:
    exchange_config = exchange_config or ExchangeConfig()

    connection = await connect(connection_url)
    async with connection:
        # Creating a channel
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            exchange_config.name,
            exchange_config.type,
        )

        # Declaring queue
        queue = await channel.declare_queue(exclusive=True)

        await queue.bind(exchange)
        await queue.consume(on_message)

        print("Listening...")

        await asyncio.Future()
