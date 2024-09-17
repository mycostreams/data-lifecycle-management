import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Awaitable, Callable

from watchfiles import Change, awatch

from prince_archiver.utils import now

from .file import AsyncFileSystem, EventFile, SystemDir

LOGGER = logging.getLogger(__name__)


class EventIngester:
    def __init__(
        self,
        system_dirs: list[SystemDir],
        handler: Callable[[EventFile], Awaitable[None]],
        *,
        file_system: AsyncFileSystem | None = None,
    ):
        self.system_dirs = system_dirs
        self.ingester = handler
        self.file_system = file_system

    async def ingest_backlog(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ):
        end = now()
        start = start or (end - timedelta(hours=12))

        LOGGER.info("Ingesting backlog")
        for sys_dir in self.system_dirs:
            async for file_info in sys_dir.iter_events():
                if start < file_info.timestamp < end:
                    await self.ingester(file_info)

    async def ingest_latest(self, stop_event: asyncio.Event | None = None):
        LOGGER.info("Ingesting latest")
        watcher = awatch(
            *(sys_dir.events_dir for sys_dir in self.system_dirs),
            stop_event=stop_event,
            watch_filter=self._added_filter,
            recursive=False,
        )
        async for changes in watcher:
            for _, _filepath in changes:
                await self.ingester(
                    self._get_event_file_info(Path(_filepath)),
                )

    def _get_event_file_info(self, path: Path) -> EventFile:
        for system_dir in self.system_dirs:
            if system_dir.is_relative(path):
                return EventFile(
                    path=path,
                    system_dir=system_dir,
                    file_system=self.file_system or system_dir.file_system,
                )
        raise ValueError()

    @staticmethod
    def _added_filter(change: Change, path: str) -> bool:
        return change == Change.added and Path(path).exists()


async def worker(
    handler: Callable[[EventFile], Awaitable[None]],
    queue: asyncio.Queue[EventFile],
):
    while True:
        event_file_info = await queue.get()
        await handler(event_file_info)
        queue.task_done()


class EventQueueManager:
    def __init__(self, queue: asyncio.Queue[EventFile]):
        self._queue = queue

    async def add(self, event: EventFile):
        self._queue.put_nowait(event)


@asynccontextmanager
async def managed_event_queue(
    handler: Callable[[EventFile], Awaitable[None]],
    queue: asyncio.Queue[EventFile] | None = None,
    worker_count: int = 5,
):
    queue = queue or asyncio.Queue[EventFile]()

    tasks = [asyncio.create_task(worker(handler, queue)) for _ in range(worker_count)]

    yield EventQueueManager(queue)

    await queue.join()

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)