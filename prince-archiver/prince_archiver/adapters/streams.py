from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, auto
from typing import AsyncGenerator

from redis.asyncio import Redis

from prince_archiver.service_layer.messages import ImagingEventStream

ReadGroupResponseT = list[tuple[str, list[tuple[str, dict[bytes, bytes]]]]]


class Streams(StrEnum):
    new_imaging_event = "data-ingester:new-imaging-event"


class Group(StrEnum):
    delete_src = auto()
    delete_staging = auto()
    export_event = auto()
    import_event = auto()


@dataclass
class ConsumerGroup:
    group_name: str
    consumer_name: str


class Stream:
    def __init__(self, redis: Redis, stream: str):
        self.redis = redis
        self.stream = stream

    async def stream_group(
        self,
        group: ConsumerGroup,
    ) -> AsyncGenerator[tuple[str, ImagingEventStream], None]:
        stream_id: int | str = 0
        while True:
            value: ReadGroupResponseT = await self.redis.xreadgroup(
                groupname=group.group_name,
                consumername=group.consumer_name,
                streams={self.stream: stream_id},
            )

            # Occurs when there are no latest messages (e.g >)
            if not value:
                continue

            # Occurs when backlog fully processed
            _, msgs = value[0]
            if not msgs:
                stream_id = ">"

            for id, raw_payload in msgs:
                payload = ImagingEventStream.model_validate_json(raw_payload[b"data"])
                yield id, payload

    async def add(self, msg: ImagingEventStream):
        await self.redis.xadd(self.stream, {"data": msg.model_dump_json()})

    async def trim(self, datetime: datetime):
        await self.redis.xtrim(self.stream, minid=int(datetime.timestamp()))

    async def ack(self, id: str, group: ConsumerGroup):
        await self.redis.xack(self.stream, group.group_name, id)
