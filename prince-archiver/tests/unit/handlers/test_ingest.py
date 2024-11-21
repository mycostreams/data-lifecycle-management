from dataclasses import dataclass
from uuid import uuid4

import pytest

from prince_archiver.domain.models import ImagingEvent
from prince_archiver.service_layer.dto import (
    ImportedImagingEvent,
    ImportImagingEvent,
)
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.state import import_imaging_event

from .utils import MockUnitOfWork


@dataclass
class _MsgKwargs:
    system: str
    experiment_id: str
    type: str
    timestamp: str
    src_dir_info: dict
    metadata: dict


@pytest.fixture()
def msg_kwargs(metadata: dict) -> _MsgKwargs:
    """
    Kwargs which can be passed into `ImportImagingEvent` and `ImportImagingEvent`.
    """
    return _MsgKwargs(
        system="prince",
        experiment_id="test_id",
        timestamp="2000-01-01T00:00:00+00:00",
        type="stitch",
        src_dir_info={
            "local_path": "test/path",
            "img_count": 1,
        },
        metadata=metadata,
    )


async def test_import_imaging_event_successful(
    msg_kwargs: _MsgKwargs,
    uow: MockUnitOfWork,
):
    ref_id = uuid4()

    msg = ImportImagingEvent(ref_id=ref_id, **msg_kwargs.__dict__)

    await import_imaging_event(msg, uow)

    imaging_event = await uow.imaging_events.get_by_ref_id(ref_id)
    assert isinstance(imaging_event, ImagingEvent)

    next_msg = next(uow.collect_messages())
    assert isinstance(next_msg, ImportedImagingEvent)

    assert uow.is_commited


async def test_import_imaging_event_already_imported(
    msg_kwargs: _MsgKwargs,
    uow: MockUnitOfWork,
    unexported_imaging_event: ImagingEvent,
):
    msg = ImportImagingEvent(
        ref_id=unexported_imaging_event.ref_id,
        **msg_kwargs.__dict__,
    )
    with pytest.raises(ServiceLayerException):
        await import_imaging_event(msg, uow)
