import asyncio
from datetime import UTC, datetime
from typing import Awaitable, Callable
from uuid import uuid4

import pytest
from redis.asyncio import Redis
from testcontainers.redis import AsyncRedisContainer

from prince_archiver.adapters.streams import (
    AbstractIncomingMessage,
    AbstractMessage,
    ConsumerGroup,
    Stream,
)


class Message(AbstractMessage):
    def __init__(self, data: dict):
        self.data = data

    def fields(self) -> dict:
        return self.data


@pytest.fixture(name="redis_container", scope="module")
def fixture_redis_container():
    with AsyncRedisContainer() as container:
        yield container


@pytest.fixture(name="stream_name")
def fixture_stream_name() -> str:
    return uuid4().hex


@pytest.fixture(name="redis")
async def fixture_redis(stream_name: str, redis_container: AsyncRedisContainer):
    redis = await redis_container.get_async_client()

    await redis.xgroup_create(
        name=stream_name,
        groupname="test",
        id=0,
        mkstream=True,
    )

    yield redis

    await redis.xtrim(stream_name, minid=0)
    await redis.aclose()


@pytest.fixture(name="stream")
def fixture_stream(stream_name: str, redis: Redis) -> Stream:
    return Stream(redis, stream_name)


@pytest.fixture(name="message_factory")
def fixture_message_factory(
    redis: Redis,
    stream_name: str,
) -> Callable[[str, dict], Awaitable[str]]:
    async def _add_message(id: str, fields: dict) -> str:
        return await redis.xadd(stream_name, fields, id)

    return _add_message


async def test_stream_backlog(
    stream: Stream,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    payload = {"hex": uuid4().hex}
    await message_factory("*", payload)

    streamer = stream.stream_group(
        ConsumerGroup("test", "test"),
        msg_cls=AbstractIncomingMessage,
    )

    assert (msg := await asyncio.wait_for(anext(streamer), 2))
    assert msg.raw_data == {k.encode(): v.encode() for k, v in payload.items()}


async def test_stream_latest(
    stream: Stream,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    streamer = stream.stream_group(
        ConsumerGroup("test", "test"),
        msg_cls=AbstractIncomingMessage,
    )

    payload = {"hex": uuid4().hex}
    await message_factory("*", payload)

    assert (msg := await asyncio.wait_for(anext(streamer), 2))
    assert msg.raw_data == {k.encode(): v.encode() for k, v in payload.items()}


async def test_add(stream: Stream, redis: Redis):
    assert await redis.xlen(stream.stream) == 0

    await stream.add(Message({"a": "b"}))

    assert await redis.xlen(stream.stream) == 1


async def test_trim(
    stream: Stream,
    redis: Redis,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    payload = {"a": "b"}

    await message_factory(
        f"{datetime(1999, 1, 1, tzinfo=UTC).timestamp():.0f}",
        payload,
    )
    await message_factory(
        f"{datetime(2001, 1, 1, tzinfo=UTC).timestamp():.0f}",
        payload,
    )

    assert await redis.xlen(stream.stream) == 2

    await stream.trim(datetime(2000, 1, 1, tzinfo=UTC))

    assert await redis.xlen(stream.stream) == 1


async def test_can_acknowledge_message(
    stream: Stream,
    redis: Redis,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    id = await message_factory("*", {"a": "b"})

    response = await redis.xreadgroup(
        groupname="test",
        consumername="test",
        streams={stream.stream: ">"},
    )

    response: dict = await redis.xpending(stream.stream, "test")
    assert response["pending"] == 1

    await stream.ack(id, "test")

    response: dict = await redis.xpending(stream.stream, "test")
    assert response["pending"] == 0


async def test_range(
    stream: Stream,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    payload = {"a": "b"}

    t1 = datetime(1999, 1, 1, tzinfo=UTC)
    t2 = datetime(2001, 1, 1, tzinfo=UTC)

    await message_factory(f"{t1.timestamp():.0f}", payload)
    id = await message_factory(f"{t2.timestamp():.0f}", payload)

    iterator = stream.range(
        start=datetime(2000, 1, 1, tzinfo=UTC),
        end=datetime.now(),
        msg_cls=AbstractIncomingMessage,
    )

    msgs = [item async for item in iterator]

    assert len(msgs) == 1
    assert {msg.id for msg in msgs} == {id}
