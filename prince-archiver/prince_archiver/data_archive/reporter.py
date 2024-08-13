import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

import httpx
from jinja2 import Environment, PackageLoader
from pydantic import BaseModel, Field, HttpUrl
from s3fs import S3FileSystem

from prince_archiver.definitions import EventType
from prince_archiver.service_layer.uow import UnitOfWork

LOGGER = logging.getLogger(__name__)


class Event(BaseModel):
    timestep_id: UUID
    experiment_id: str
    key: str
    timestamp: datetime
    event_type: EventType = Field(default=EventType.STITCH)
    url: HttpUrl


class Message(StrEnum):
    DAILY_REPORT = "daily-report.json.jinja"


class Messenger:
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        _env: Environment | None = None,
    ):
        self.client = client
        self.url = url

        self.env = _env or Environment(
            loader=PackageLoader("prince_archiver"),
            enable_async=True,
        )

    async def _render_message(self, message: Message, **kwargs: Any):
        template = self.env.get_template(message.value)
        return await template.render_async(**kwargs)

    async def publish(self, message: Message, **kwargs: Any):
        await self.client.post(
            self.url,
            json=json.loads(
                await self._render_message(message, **kwargs),
            ),
        )


class Reporter:
    def __init__(
        self,
        s3: S3FileSystem,
        *,
        messenger: Messenger | None = None,
    ):
        self.s3 = s3
        self.messenger = messenger

        # TODO: make configurable
        self.timeout = timedelta(days=3)  # 1 day

    async def generate_report(
        self,
        uow: UnitOfWork,
        *,
        date: date,
        target: str,
    ):
        async with (
            uow,
            asyncio.TaskGroup() as tg,
        ):
            task = tg.create_task(self._get_url(target))
            entries = await self._get_events(uow, date)
            tg.create_task(self._write_events(entries, target))

        await self._notify(task.result(), img_count=len(entries), date=date)

    async def _notify(self, url: str, img_count: int, date: date):
        if self.messenger:
            await self.messenger.publish(
                Message.DAILY_REPORT,
                date=date.isoformat(),
                url=url,
                img_count=img_count,
            )

    async def _get_events(self, uow: UnitOfWork, date: date) -> list[Event]:
        timestamps = list(
            filter(
                lambda t: t.object_store_entry,
                await uow.timestamps.get_by_date(date),
            ),
        )

        event_kwargs: list[tuple[dict, asyncio.Task[str]]] = []
        async with asyncio.TaskGroup() as tg:
            for event in timestamps:
                assert event.object_store_entry

                base_kwargs = {
                    "timestep_id": event.timestep_id,
                    "experiment_id": event.experiment_id,
                    "key": event.object_store_entry.key,
                    "timestamp": event.timestamp,
                }
                url_task = tg.create_task(self._get_url(event.object_store_entry.key))

                event_kwargs.append((base_kwargs, url_task))

        return [Event(**_kwargs, url=_url.result()) for _kwargs, _url in event_kwargs]

    async def _write_events(self, entries: list[Event], target: str):
        data = json.dumps(
            [e.model_dump(mode="json") for e in entries],
            indent=4,
        )
        await self.s3._pipe_file(target, data)

    async def _get_url(self, target: str, *, timeout: int | None = None) -> str:
        url: str = await self.s3._url(
            target,
            timeout or self.timeout.total_seconds(),
        )
        return url
