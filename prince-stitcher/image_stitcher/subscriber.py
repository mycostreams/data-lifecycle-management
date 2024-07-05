import asyncio
import os
from typing import Awaitable, Callable

import redis.asyncio as redis
from redis.asyncio.client import PubSub

from .handler import Handler, Message
from .log import configure_logging


class Settings:
    REDIS_DSN: str
    CHANNEL: str
    DATA_DIR: str


async def worker(
    channel: PubSub,
    handler: Callable[[Message], Awaitable[None]],
):
    while True:
        message = await channel.get_message(ignore_subscribe_messages=True)
        if message is not None:
            parsed_msg = Message.model_validate_json(message["data"])
            await handler(parsed_msg)


async def main():
    configure_logging()

    redis_conn = redis.from_url(os.getenv("REDIS_DSN"))

    async with (
        Handler() as handler,
        redis_conn.pubsub() as pubsub,
    ):
        await pubsub.subscribe("archiver:timestep")
        await worker(pubsub, handler)


if __name__ == "__main__":
    asyncio.run(main())
