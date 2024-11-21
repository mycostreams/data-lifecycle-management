import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Awaitable, Callable, Generic, Type, TypeVar
from uuid import uuid4

from redis.asyncio import Redis

LOGGER = logging.getLogger(__name__)

ResponseT = list[tuple[str, list[tuple[bytes, dict[bytes, bytes]]]]]

T = TypeVar("T")


def get_id(dt: datetime) -> int:
    return int(dt.timestamp() * 1e3)


@dataclass
class Consumer:
    group_name: str
    consumer_name: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class MessageInfo:
    id: str
    stream_name: str
    group_name: str | None = None


class AbstractOutgoingMessage(ABC):
    @abstractmethod
    def fields(self) -> dict: ...


class AbstractIncomingMessage(Generic[T], ABC):
    def __init__(
        self,
        id: bytes | str,
        stream_name: str,
        group_name: str | None,
        raw_data: dict[bytes, bytes],
        stream: "Stream",
    ):
        self.id = id
        self.stream_name = stream_name
        self.group_name = group_name
        self.raw_data = raw_data
        self.stream = stream

    @property
    def info(self):
        return MessageInfo(
            id=self.id,
            stream_name=self.stream_name,
            group_name=self.group_name,
        )

    @abstractmethod
    def processed_data(self) -> T: ...

    @asynccontextmanager
    async def process(self):
        try:
            yield
        except Exception as e:
            raise e
        else:
            await self.stream.ack(self.info)


AbstractIncomingMessageT = TypeVar(
    "AbstractIncomingMessageT",
    bound=AbstractIncomingMessage,
)


class Stream:
    def __init__(self, redis: Redis, name: str, *, max_len: int | None = None):
        self.name = name
        self.redis = redis

        self.max_len = max_len

    async def range(
        self,
        start: datetime,
        end: datetime,
        *,
        msg_cls: Type[AbstractIncomingMessageT],
    ) -> AsyncGenerator[AbstractIncomingMessageT, None]:
        response: list[tuple[bytes, dict[bytes, bytes]]] = await self.redis.xrange(
            name=self.name,
            min=get_id(start),
            max=get_id(end),
        )
        for id, raw_payload in response:
            yield msg_cls(
                id=id,
                raw_data=raw_payload,
                stream_name=self.name,
                group_name=None,
                stream=self,
            )

    async def stream_group(
        self,
        consumer: Consumer,
        *,
        msg_cls: Type[AbstractIncomingMessageT],
        stop_event: asyncio.Event | None = None,
    ) -> AsyncGenerator[AbstractIncomingMessageT, None]:
        stream_id: int | str = 0
        stop_event = stop_event or asyncio.Event()

        LOGGER.info("Consuming `%s`", self.name)
        while not stop_event.is_set():
            response: ResponseT = await self.redis.xreadgroup(
                groupname=consumer.group_name,
                consumername=consumer.consumer_name,
                streams={self.name: stream_id},
                count=1,
                block=2000,
            )

            # Occurs when there are no latest messages (e.g >)
            if not response:
                continue

            # Occurs when backlog fully processed
            _, msgs = response[0]
            if not msgs:
                stream_id = ">"

            for id, raw_payload in msgs:
                yield msg_cls(
                    id=id,
                    stream_name=self.name,
                    group_name=consumer.group_name,
                    raw_data=raw_payload,
                    stream=self,
                )

    async def add(self, msg: AbstractOutgoingMessage):
        await self.redis.xadd(self.name, msg.fields(), maxlen=self.max_len)

    async def ack(self, message_info: MessageInfo):
        if message_info.group_name:
            await self.redis.xack(self.name, message_info.group_name, message_info.id)

    async def trim(self, datetime: datetime):
        await self.redis.xtrim(
            self.name,
            approximate=False,
            minid=get_id(datetime),
        )


class AbstractIngester(ABC):
    def __init__(
        self,
        streamer: AsyncGenerator[AbstractIncomingMessageT, None],
        handler: Callable[[AbstractIncomingMessageT], Awaitable[None]],
    ):
        self.streamer = streamer
        self.handler = handler

    @abstractmethod
    async def consume(self): ...

    @asynccontextmanager
    async def managed_consumer(self):
        task = asyncio.create_task(self.consume())

        yield

        await task
