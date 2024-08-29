from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from s3fs import S3FileSystem

from prince_archiver.adapters.file import ArchiveFileManager
from prince_archiver.definitions import EventType
from prince_archiver.domain.models import ImagingEvent
from prince_archiver.domain.value_objects import Checksum
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.exporter import (
    ExportHandler,
    persist_imaging_event_export,
)
from prince_archiver.service_layer.messages import (
    ExportedImagingEvent,
    ExportImagingEvent,
)

from .utils import MockUnitOfWork


async def test_export_handler_successful(
    mock_file_manager: ArchiveFileManager, uow: MockUnitOfWork
):
    handler = ExportHandler(
        s3=AsyncMock(S3FileSystem),
        key_generator=lambda _: "test/key.tar",
        file_manager=mock_file_manager,
    )

    msg = ExportImagingEvent(
        ref_id=uuid4(),
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
        experiment_id="test_experiment_id",
        type=EventType.STITCH,
        target_key="target/key",
        local_path=Path("test"),
    )

    await handler(msg, uow)

    msg = next(uow.collect_messages())

    assert isinstance(msg, ExportedImagingEvent)
    assert msg.checksum == Checksum(hex="test")
    assert msg.size == 1024
    assert msg.key == "test/key.tar"

    assert uow.is_commited


async def test_persist_imaging_event_successful(
    uow: MockUnitOfWork,
    unexported_imaging_event: ImagingEvent,
):
    msg = ExportedImagingEvent(
        ref_id=unexported_imaging_event.ref_id,
        checksum=Checksum("test"),
        size=1024,
        key="target",
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
    )

    await persist_imaging_event_export(msg, uow)

    assert unexported_imaging_event.event_archive
    assert unexported_imaging_event.object_store_entry

    assert uow.is_commited


async def test_persist_imaging_event_non_existent_reference():
    msg = ExportedImagingEvent(
        ref_id=uuid4(),
        checksum=Checksum("test"),
        size=1024,
        key="target",
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(ServiceLayerException):
        await persist_imaging_event_export(msg, MockUnitOfWork())
