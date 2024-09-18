import asyncio
from unittest.mock import AsyncMock

from prince_archiver.adapters.file import EventFile
from prince_archiver.adapters.ingester import managed_event_queue


class MockHandler:
    def __init__(self):
        self.events = set[EventFile]()

    async def __call__(self, event: EventFile):
        self.events.add(event)


async def test_managed_event_queue_processes_events():
    handler = MockHandler()

    first_event = AsyncMock(EventFile)
    second_event = AsyncMock(EventFile)

    queue = asyncio.Queue[EventFile]()
    queue.put_nowait(first_event)

    async with managed_event_queue(handler=handler, queue=queue) as queue_manager:
        await queue_manager.add(second_event)

    assert queue.empty()
    assert handler.events == {first_event, second_event}
