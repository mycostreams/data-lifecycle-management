import asyncio
from unittest.mock import AsyncMock

from prince_archiver.adapters.ingester import EventIngester
from prince_archiver.entrypoints.event_ingester.ingester import (
    managed_background_event_ingester,
)


async def test_managed_background_event_ingester():
    mock_ingester = AsyncMock(EventIngester)
    stop_event = asyncio.Event()

    async with managed_background_event_ingester(mock_ingester, stop_event=stop_event):
        pass

    mock_ingester.ingest_backlog.assert_awaited_once_with()
    mock_ingester.ingest_latest.assert_awaited_once_with(stop_event=stop_event)

    assert stop_event.is_set()
