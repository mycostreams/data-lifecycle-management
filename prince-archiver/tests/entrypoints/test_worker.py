from datetime import date
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from aio_pika.abc import AbstractIncomingMessage

from prince_archiver.entrypoints.worker.external import (
    SubscriberMessageHandler,
)
from prince_archiver.service_layer.external_dto import Archive, UpdateArchiveEntries
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import AddDataArchiveEntry, ArchiveMember


@pytest.fixture(name="update_archive_entries_msg")
def fixture_update_archive_entries_msg() -> UpdateArchiveEntries:
    return UpdateArchiveEntries(
        job_id=UUID("a136586a44e6417eb707e10d9795b1f9"),
        date=date(2000, 1, 1),
        archives=[
            Archive(
                id=UUID("dabfa4a3051c4e47a736e9d12e38b05a"),
                path="test_path",
                src_keys=["test/a"],
            )
        ],
    )


async def test_subscriber_message_handler(
    update_archive_entries_msg: UpdateArchiveEntries,
):
    messagebus = AsyncMock(MessageBus)
    handler = SubscriberMessageHandler(messagebus_factory=lambda: messagebus)

    incoming_message = AsyncMock(
        AbstractIncomingMessage,
        body=update_archive_entries_msg.model_dump_json().encode(),
    )

    expected_msg = AddDataArchiveEntry(
        id=UUID("dabfa4a3051c4e47a736e9d12e38b05a"),
        job_id=UUID("a136586a44e6417eb707e10d9795b1f9"),
        path="test_path",
        members=[ArchiveMember(src_key="test/a", member_key="a")],
    )

    await handler(incoming_message)
    messagebus.handle.assert_awaited_once_with(expected_msg)
