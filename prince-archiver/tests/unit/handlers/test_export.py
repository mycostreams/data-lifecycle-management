from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from arq import ArqRedis
from s3fs import S3FileSystem

from prince_archiver.adapters.file import PathManager
from prince_archiver.definitions import Algorithm, EventType
from prince_archiver.domain.models import ImagingEvent
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.export import (
    ExportHandler,
    persist_imaging_event_export,
)
from prince_archiver.service_layer.messages import (
    Checksum,
    ExportedImagingEvent,
    ExportImagingEvent,
)

from .utils import MockUnitOfWork


async def test_export_handler_successful(mock_path_manager: PathManager):
    mock_redis = AsyncMock(ArqRedis)

    handler = ExportHandler(
        redis=mock_redis,
        s3=AsyncMock(S3FileSystem),
        key_generator=lambda _: "test/key.tar",
        path_manager=mock_path_manager,
    )

    msg = ExportImagingEvent(
        ref_id=uuid4(),
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
        experiment_id="test_experiment_id",
        type=EventType.STITCH,
        target_key="target/key",
        local_path=Path("test"),
    )

    await handler(msg)

    # TODO: Improve
    mock_redis.enqueue_job.assert_awaited_once()


async def test_persist_imaging_event_successful(
    uow: MockUnitOfWork,
    unexported_imaging_event: ImagingEvent,
):
    msg = ExportedImagingEvent(
        ref_id=unexported_imaging_event.ref_id,
        checksum=Checksum(hex="test", algorithm=Algorithm.SHA256),
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
        checksum=Checksum(hex="test", algorithm=Algorithm.SHA256),
        size=1024,
        key="target",
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(ServiceLayerException):
        await persist_imaging_event_export(msg, MockUnitOfWork())
