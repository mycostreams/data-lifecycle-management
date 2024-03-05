import asyncio
import logging

from aio_pika import ExchangeType, connect
from aio_pika.abc import AbstractIncomingMessage

LOGGER = logging.getLogger(__name__)


async def on_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        print(f"[x] {message.body!r}")


async def subscriber(
    *,
    connection_url: str = "amqp://guest:guest@localhost/",
) -> None:

    # Perform connection
    connection = await connect(connection_url)

    async with connection:
        # Creating a channel
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            "slurm-uploader",
            ExchangeType.FANOUT,
        )

        # Declaring queue
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange)
        await queue.consume(on_message)

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(subscriber())
