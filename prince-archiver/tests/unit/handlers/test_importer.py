from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from arq import ArqRedis

from prince_archiver.definitions import EventType, System
from prince_archiver.domain.models import StitchEvent
from prince_archiver.domain.value_objects import GridSize, Location
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.importer import (
    Context,
    import_imaging_event,
    propagate_new_imaging_event,
)
from prince_archiver.service_layer.messages import (
    ImagingParams,
    ImportedImagingEvent,
    ImportImagingEvent,
)

from .utils import MockUnitOfWork


@dataclass
class _MsgKwargs:
    experiment_id: str
    local_path: str
    timestamp: datetime
    location: Location
    params: ImagingParams


@pytest.fixture()
def msg_kwargs() -> _MsgKwargs:
    """
    Kwargs which can be passed into `ImportImagingEvent` and `ImportedImagingEvent`.
    """
    return _MsgKwargs(
        experiment_id="test_id",
        local_path="test_path",
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
        location=Location(
            system=System.PRINCE,
            position=1,
        ),
        params=ImagingParams(
            type=EventType.STITCH,
            grid_size=GridSize(row=10, col=10),
        ),
    )


async def test_import_imaging_event_successful(
    msg_kwargs: _MsgKwargs,
    uow: MockUnitOfWork,
):
    ref_id = uuid4()

    msg = ImportImagingEvent(
        ref_id=ref_id,
        **msg_kwargs.__dict__,
    )
    await import_imaging_event(msg, uow)

    imaging_event = await uow.imaging_events.get_by_ref_id(ref_id)
    assert isinstance(imaging_event, StitchEvent)

    next_msg = next(uow.collect_messages())
    assert isinstance(next_msg, ImportedImagingEvent)

    assert uow.is_commited


async def test_import_imaging_event_already_imported(
    msg_kwargs: _MsgKwargs,
    uow: MockUnitOfWork,
    unexported_stitch_event: StitchEvent,
):
    msg = ImportImagingEvent(
        ref_id=unexported_stitch_event.ref_id,
        **msg_kwargs.__dict__,
    )
    with pytest.raises(ServiceLayerException):
        await import_imaging_event(msg, uow)


async def test_propagate_new_imaging_event(
    msg_kwargs: _MsgKwargs,
):
    ref_id = uuid4()
    mock_redis = AsyncMock(ArqRedis)

    msg = ImportedImagingEvent(ref_id=ref_id, id=uuid4(), **msg_kwargs.__dict__)

    await propagate_new_imaging_event(
        msg, MockUnitOfWork(), context=Context(redis_client=mock_redis)
    )

    mock_redis.enqueue_job.assert_awaited_once_with(
        "workflow",
        {"ref_id": str(msg.ref_id), "type": EventType.STITCH},
    )
