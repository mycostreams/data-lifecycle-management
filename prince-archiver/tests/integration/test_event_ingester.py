import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4

import pytest

from prince_archiver.adapters.file import AsyncFileSystem, EventFile, SystemDir
from prince_archiver.adapters.ingester import EventIngester
from prince_archiver.definitions import System

pytestmark = pytest.mark.integration


class MockHandler:
    def __init__(self, event: asyncio.Event | None = None):
        self.event = event or asyncio.Event()
        self.messages: list[EventFile] = []

    async def handler(self, event: EventFile):
        self.event.set()
        self.messages.append(event)


@pytest.fixture()
def mock_handler() -> MockHandler:
    return MockHandler()


@pytest.fixture(name="src_dir")
def fixture_src_dir(tmp_path: Path) -> Path:
    src_dir = tmp_path / uuid4().hex
    return src_dir


@pytest.fixture(name="event_file_factory")
def fixture_event_file_factory(src_dir: Path) -> Callable[[datetime], Path]:
    event_path = src_dir / "events"
    event_path.mkdir(parents=True)

    def _event_file_factory(dt: datetime) -> Path:
        timestamp = dt.timestamp()
        event_file_path = event_path / f"{timestamp:.0f}.json"
        event_file_path.write_text("{}")
        return event_file_path

    return _event_file_factory


@pytest.fixture(name="event_ingester")
def fixture_event_ingester(src_dir: Path, mock_handler: MockHandler) -> EventIngester:
    return EventIngester(
        system_dirs=[
            SystemDir(
                system=System.PRINCE,
                path=src_dir,
                file_system=AsyncFileSystem(),
            )
        ],
        handler=mock_handler.handler,
    )


async def test_ingest_latest(
    event_ingester: EventIngester,
    event_file_factory: Callable[[datetime], Path],
    mock_handler: MockHandler,
):
    start_event = asyncio.Event()

    ingester = event_ingester.ingest_latest(
        start_event=start_event, stop_event=mock_handler.event
    )

    async with asyncio.TaskGroup() as tg:
        tg.create_task(asyncio.wait_for(ingester, 2.0))

        await start_event.wait()

        event_file_path = event_file_factory(datetime.now())

    assert len(mock_handler.messages) == 1
    assert event_file_path in {msg.path for msg in mock_handler.messages}


async def test_ingest_backlog(
    event_ingester: EventIngester,
    event_file_factory: Callable[[datetime], Path],
    mock_handler: MockHandler,
):
    start_time = datetime(2000, 1, 1, tzinfo=UTC)

    excluded = datetime(1999, 1, 1, tzinfo=UTC)
    included = datetime(2001, 1, 1, tzinfo=UTC)

    mapping = {dt: event_file_factory(dt) for dt in (included, excluded)}

    await event_ingester.ingest_backlog(start=start_time)

    assert len(mock_handler.messages) == 1
    assert mapping[included] in {msg.path for msg in mock_handler.messages}
