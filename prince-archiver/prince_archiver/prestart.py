import asyncio
import os

import redis.asyncio as redis
from redis import ResponseError

from prince_archiver.adapters.streams import Group, Streams


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
    client = redis.from_url(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )

    stream = Streams.new_imaging_event

    async with client:
        await asyncio.gather(
            *(create_group(client, stream, group) for group in Group),
        )


if __name__ == "__main__":
    asyncio.run(main())
