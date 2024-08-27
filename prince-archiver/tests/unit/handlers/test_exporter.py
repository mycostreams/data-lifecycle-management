from datetime import UTC, datetime
from pathlib import Path
from typing import Awaitable, Callable
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
    Context,
    ExportHandler,
    initiate_imaging_event_export,
    persist_imaging_event_export,
)
from prince_archiver.service_layer.messages import (
    ExportedImagingEvent,
    ExportImagingEvent,
    InitiateExportEvent,
)
from prince_archiver.service_layer.uow import AbstractUnitOfWork

from .utils import MockUnitOfWork

HandlerT = Callable[[InitiateExportEvent, AbstractUnitOfWork], Awaitable[None]]


@pytest.fixture(name="mock_file_manager")
def fixture_mock_file_manager() -> ArchiveFileManager:
    mock = AsyncMock(ArchiveFileManager)

    mock.get_archive_checksum.return_value = Checksum(hex="test")
    mock.get_archive_size.return_value = 1024
    mock.get_temp_archive.return_value.__aenter__ = AsyncMock(return_value=Path("test"))

    return mock


@pytest.fixture(name="context_bound_handler")
def fixture_context_bound_handler() -> HandlerT:
    context = Context(
        base_path=Path("/test/"),
        key_generator=lambda _: "test.tar",
    )

    def _handler(msg: InitiateExportEvent, uow: AbstractUnitOfWork):
        return initiate_imaging_event_export(msg, uow, context=context)

    return _handler


async def test_export_handler_successful(
    mock_file_manager: ArchiveFileManager, uow: MockUnitOfWork
):
    handler = ExportHandler(AsyncMock(S3FileSystem), mock_file_manager)

    msg = ExportImagingEvent(
        ref_id=uuid4(),
        type=EventType.STITCH,
        local_path=Path("test"),
        target_key="target/key",
    )

    await handler(msg, uow)

    msg = next(uow.collect_messages())

    assert isinstance(msg, ExportedImagingEvent)
    assert msg.checksum == Checksum(hex="test")
    assert msg.size == 1024
    assert msg.key == "target/key"

    assert uow.is_commited


async def test_initiate_imaging_event_export_successful(
    context_bound_handler: HandlerT,
    uow: MockUnitOfWork,
    unexported_imaging_event: ImagingEvent,
):
    msg = InitiateExportEvent(
        ref_id=unexported_imaging_event.ref_id, type=EventType.STITCH
    )

    await context_bound_handler(msg, uow)

    expected_msg = ExportImagingEvent(
        ref_id=unexported_imaging_event.ref_id,
        type=EventType.STITCH,
        local_path=Path("/test/unexported/path"),
        target_key="test.tar",
    )

    assert next(uow.collect_messages()) == expected_msg


async def test_initiate_imaging_event_export_non_existent_reference(
    context_bound_handler: HandlerT,
):
    msg = InitiateExportEvent(
        ref_id=uuid4(),
        type=EventType.STITCH,
    )

    with pytest.raises(ServiceLayerException):
        await context_bound_handler(msg, MockUnitOfWork())


async def test_initiate_imaging_event_already_exported(
    context_bound_handler: HandlerT,
    uow: MockUnitOfWork,
    exported_imaging_event: ImagingEvent,
):
    msg = InitiateExportEvent(
        ref_id=exported_imaging_event.ref_id,
        type=EventType.STITCH,
    )

    with pytest.raises(ServiceLayerException):
        await context_bound_handler(msg, uow)


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
