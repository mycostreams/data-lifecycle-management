from datetime import UTC, datetime
from uuid import uuid4

import pytest

from prince_archiver.definitions import Algorithm
from prince_archiver.domain.models import ImagingEvent
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.state import persist_imaging_event_export
from prince_archiver.service_layer.messages import (
    Checksum,
    ExportedImagingEvent,
)

from .utils import MockUnitOfWork


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
