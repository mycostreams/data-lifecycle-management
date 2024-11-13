import asyncio
from datetime import UTC, datetime
from typing import Awaitable, Callable
from uuid import uuid4

import pytest
from redis.asyncio import Redis
from testcontainers.redis import AsyncRedisContainer

from prince_archiver.adapters.streams import (
    AbstractIncomingMessage,
    AbstractOutgoingMessage,
    Consumer,
    MessageInfo,
    Stream,
    get_id,
)


class MockIncomingMessage(AbstractIncomingMessage[dict[str, str]]):
    def processed_data(self) -> dict[str, str]:
        return {k.decode(): v.decode() for k, v in self.raw_data.items()}


class Message(AbstractOutgoingMessage):
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
        Consumer("test", "test"),
        msg_cls=MockIncomingMessage,
    )

    assert (msg := await asyncio.wait_for(anext(streamer), 2))
    assert msg.processed_data() == payload


async def test_stream_latest(
    stream: Stream,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    streamer = stream.stream_group(
        Consumer("test", "test"),
        msg_cls=MockIncomingMessage,
    )

    payload = {"hex": uuid4().hex}
    await message_factory("*", payload)

    assert (msg := await asyncio.wait_for(anext(streamer), 2))
    assert msg.processed_data() == payload


async def test_add(stream: Stream, redis: Redis):
    assert await redis.xlen(stream.name) == 0

    await stream.add(Message({"a": "b"}))

    assert await redis.xlen(stream.name) == 1


async def test_trim(
    stream: Stream,
    redis: Redis,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    payload = {"a": "b"}

    await message_factory(get_id(datetime(1999, 1, 1, tzinfo=UTC)), payload)
    await message_factory(get_id(datetime(2001, 1, 1, tzinfo=UTC)), payload)

    assert await redis.xlen(stream.name) == 2

    await stream.trim(datetime(2000, 1, 1, tzinfo=UTC))

    assert await redis.xlen(stream.name) == 1


async def test_can_acknowledge_message(
    stream: Stream,
    redis: Redis,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    id = await message_factory("*", {"a": "b"})

    response = await redis.xreadgroup(
        groupname="test",
        consumername="test",
        streams={stream.name: ">"},
    )

    response: dict = await redis.xpending(stream.name, "test")
    assert response["pending"] == 1

    await stream.ack(MessageInfo(id=id, stream_name="test", group_name="test"))

    response: dict = await redis.xpending(stream.name, "test")
    assert response["pending"] == 0


async def test_range(
    stream: Stream,
    message_factory: Callable[[str, dict], Awaitable[str]],
):
    payload = {"a": "b"}

    await message_factory(get_id(datetime(1999, 1, 1, tzinfo=UTC)), payload)
    id = await message_factory(get_id(datetime(2001, 1, 1, tzinfo=UTC)), payload)

    iterator = stream.range(
        start=datetime(2000, 1, 1, tzinfo=UTC),
        end=datetime.now(),
        msg_cls=MockIncomingMessage,
    )

    msgs = [item async for item in iterator]

    assert len(msgs) == 1
    assert {msg.id for msg in msgs} == {id}
