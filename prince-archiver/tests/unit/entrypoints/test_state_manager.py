from unittest.mock import AsyncMock

import pytest
from aio_pika.abc import AbstractIncomingMessage

from prince_archiver.entrypoints.state_manager.consumers import SubscriberMessageHandler
from prince_archiver.service_layer.dto import (
    AddDataArchiveEntry,
    NewDataArchiveEntries,
)
from prince_archiver.service_layer.messagebus import MessageBus


@pytest.fixture(name="new_data_archive_entries")
def fixture_new_data_archive_entries_msg() -> NewDataArchiveEntries:
    return NewDataArchiveEntries(
        job_id="a136586a44e6417eb707e10d9795b1f9",
        date="2000-01-01",
        archives=[
            {
                "id": "dabfa4a3051c4e47a736e9d12e38b05a",
                "path": "test_path",
                "src_keys": ["test/a"],
            }
        ],
    )


async def test_subscriber_message_handler(
    new_data_archive_entries: NewDataArchiveEntries,
):
    messagebus = AsyncMock(MessageBus)
    handler = SubscriberMessageHandler(messagebus_factory=lambda: messagebus)

    incoming_message = AsyncMock(
        AbstractIncomingMessage,
        body=new_data_archive_entries.model_dump_json().encode(),
    )

    expected_msg = AddDataArchiveEntry(
        id="dabfa4a3051c4e47a736e9d12e38b05a",
        job_id="a136586a44e6417eb707e10d9795b1f9",
        path="test_path",
        members=[{"src_key": "test/a", "member_key": "a"}],
    )

    await handler(incoming_message)
    messagebus.handle.assert_awaited_once_with(expected_msg)
