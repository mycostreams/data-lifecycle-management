import asyncio
import logging
import os
from datetime import UTC, datetime

import redis.asyncio as redis
from redis import ResponseError

from prince_archiver.adapters.streams import Consumer, Stream
from prince_archiver.service_layer.exceptions import InvalidStreamMessage
from prince_archiver.service_layer.streams import IncomingMessage


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


async def create_group(redis: redis.Redis, stream: str, group_name: str):
    try:
        await redis.xgroup_create(
            name=stream,
            groupname=group_name,
            id=0,
            mkstream=True,
        )
    except ResponseError:
        pass


async def main():
    logging.info("hello")

    stream_name = "data-lifecycle-management:imaging-events"
    consumer = Consumer(group_name="state-manager")

    client = redis.from_url(os.getenv("REDIS_DSN", "redis://localhost:6380"))

    async with client:
        await create_group(client, stream_name, consumer.group_name)

        stream = Stream(client, stream_name)
        streamer = stream.range(
            start=datetime(2024, 11, 19, 13, 52, tzinfo=UTC),
            end=datetime(2024, 11, 19, 13, 54, tzinfo=UTC),
            msg_cls=IncomingMessage,
        )

        async for msg in streamer:
            logging.info("Processing message %s", msg.id)
            try:
                msg.processed_data()
            except InvalidStreamMessage as err:
                logging.exception(err)
                continue

            logging.info("Ingested  %s", msg.id)


if __name__ == "__main__":
    asyncio.run(main())
