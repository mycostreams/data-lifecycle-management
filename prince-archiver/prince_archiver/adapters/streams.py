from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Type, TypeVar

from redis.asyncio import Redis

ResponseT = list[tuple[str, list[tuple[bytes, dict[bytes, bytes]]]]]


def get_id(dt: datetime) -> int:
    return int(dt.timestamp())


@dataclass
class ConsumerGroup:
    group_name: str
    consumer_name: str


class AbstractMessage(ABC):
    @abstractmethod
    def fields(self) -> dict: ...


class AbstractIncomingMessage:
    def __init__(
        self,
        id: bytes,
        raw_data: dict[bytes, bytes],
        *,
        stream: "Stream",
        group_name: str | None = None,
    ):
        self.id = id
        self.raw_data = raw_data
        self.stream = stream
        self.group_name = group_name

    @asynccontextmanager
    async def process(self):
        try:
            yield
        except Exception as e:
            raise e
        else:
            if self.group_name:
                await self.stream.ack(self.id, self.group_name)


AbstractIncomingMessageT = TypeVar(
    "AbstractIncomingMessageT",
    bound=AbstractIncomingMessage,
)


class Stream:
    def __init__(self, redis: Redis, stream: str):
        self.redis = redis
        self.stream = stream

    async def range(
        self,
        start: datetime,
        end: datetime,
        *,
        msg_cls: Type[AbstractIncomingMessageT],
    ) -> AsyncGenerator[AbstractIncomingMessageT, None]:
        response: list[tuple[bytes, dict[bytes, bytes]]] = await self.redis.xrange(
            name=self.stream,
            min=get_id(start),
            max=get_id(end),
        )
        for id, raw_payload in response:
            yield msg_cls(
                id=id,
                raw_data=raw_payload,
                stream=self,
            )

    async def stream_group(
        self,
        group: ConsumerGroup,
        *,
        msg_cls: Type[AbstractIncomingMessageT],
    ) -> AsyncGenerator[AbstractIncomingMessageT, None]:
        stream_id: int | str = 0
        while True:
            response: ResponseT = await self.redis.xreadgroup(
                groupname=group.group_name,
                consumername=group.consumer_name,
                streams={self.stream: stream_id},
                count=1,
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
                    raw_data=raw_payload,
                    stream=self,
                    group_name=group.group_name,
                )

    async def add(self, msg: AbstractMessage):
        await self.redis.xadd(self.stream, msg.fields())

    async def trim(self, datetime: datetime):
        await self.redis.xtrim(
            self.stream,
            approximate=False,
            minid=get_id(datetime),
        )

    async def ack(self, id: str, group_name: str):
        await self.redis.xack(self.stream, group_name, id)
