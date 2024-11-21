from uuid import uuid4

import pytest

from prince_archiver.domain.models import ImagingEvent
from prince_archiver.service_layer.dto import ExportedImagingEvent
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.state import persist_imaging_event_export

from .utils import MockUnitOfWork


async def test_persist_imaging_event_successful(
    uow: MockUnitOfWork,
    unexported_imaging_event: ImagingEvent,
):
    msg = ExportedImagingEvent(
        ref_id=unexported_imaging_event.ref_id,
        checksum={"hex": "test", "algorithm": "sha256"},
        size=1024,
        key="target",
        timestamp="2000-01-01T00:00:00+00:00",
    )

    await persist_imaging_event_export(msg, uow)

    assert unexported_imaging_event.event_archive
    assert unexported_imaging_event.object_store_entry

    assert uow.is_commited


async def test_persist_imaging_event_non_existent_reference():
    msg = ExportedImagingEvent(
        ref_id=uuid4(),
        checksum={"hex": "test", "algorithm": "sha256"},
        size=1024,
        key="target",
        timestamp="2000-01-01T00:00:00+00:00",
    )

    with pytest.raises(ServiceLayerException):
        await persist_imaging_event_export(msg, MockUnitOfWork())
