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
async def main() -> None:
    client = redis.from_url(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )

    await client.ping()

    mapping: dict[Streams, list[Group]] = {
        Streams.imaging_events: [Group.state_manager, Group.upload_worker],
        Streams.upload_events: [Group.state_manager],
    }
    groups = ((stream, group) for stream, groups in mapping.items() for group in groups)

    async with client:
        await asyncio.gather(
            *(create_group(client, *args) for args in groups),
        )


if __name__ == "__main__":
    asyncio.run(main())
