from uuid import uuid4

import pytest

from prince_archiver.domain import models
from prince_archiver.service_layer.dto import (
    AddDataArchiveEntry,
    ArchivedImagingEvent,
)
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.state import add_data_archive_entry

from .utils import MockDataArchiveEntryRepo, MockUnitOfWork


@pytest.fixture(name="data_archive_entry")
def fixture_data_archive_entry() -> models.DataArchiveEntry:
    return models.DataArchiveEntry(
        id=uuid4(),
        path="/path/",
        job_id=None,
        members=[
            models.ArchiveMember(
                member_key="/member_key/",
                src_key="test/key",
            )
        ],
    )


@pytest.fixture(name="msg")
def fixture_msg(data_archive_entry: models.DataArchiveEntry) -> AddDataArchiveEntry:
    return AddDataArchiveEntry.model_validate(
        data_archive_entry,
        from_attributes=True,
    )


async def test_add_data_archive_entry_successful(msg: AddDataArchiveEntry):
    uow = MockUnitOfWork()

    await add_data_archive_entry(msg, uow)

    assert len(uow.data_archive.entries) == 1

    expected_msg = ArchivedImagingEvent(
        src_key="test/key",
        data_archive_entry_id=msg.id,
    )

    assert next(uow.collect_messages()) == expected_msg


async def test_add_data_archive_entry_unsuccessful_when_path_exists(
    msg: AddDataArchiveEntry,
    data_archive_entry: models.DataArchiveEntry,
):
    uow = MockUnitOfWork(
        data_archive_repo=MockDataArchiveEntryRepo([data_archive_entry])
    )

    with pytest.raises(ServiceLayerException):
        await add_data_archive_entry(msg, uow)
