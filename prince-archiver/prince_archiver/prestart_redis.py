import asyncio
import os

import redis.asyncio as redis
from redis import ResponseError
from tenacity import retry, stop_after_attempt, wait_fixed

from prince_archiver.service_layer.streams import Group, Streams


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


@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(5),
)
async def main():
    client = redis.from_url(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )

    stream = Streams.new_imaging_event

    async with client:
        await client.ping()

        await asyncio.gather(
            *(create_group(client, stream, group) for group in Group),
        )


if __name__ == "__main__":
    asyncio.run(main())
