from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import BaseModel

from prince_archiver.definitions import EventType, System
from prince_archiver.domain.models import ImagingEvent
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.handlers.ingest import (
    import_imaging_event,
)
from prince_archiver.service_layer.messages import (
    ImportedImagingEvent,
    ImportImagingEvent,
)

from .utils import MockUnitOfWork


@dataclass
class _SrcDirInfo:
    staging_path: Path | None
    local_path: Path
    img_count: int
    raw_metadata: dict


class _MsgKwargs(BaseModel):
    system: System
    experiment_id: str
    type: EventType
    timestamp: datetime
    src_dir_info: _SrcDirInfo


@pytest.fixture()
def msg_kwargs() -> _MsgKwargs:
    """
    Kwargs which can be passed into `ImportImagingEvent` and `ImportedImagingEvent`.
    """
    return _MsgKwargs(
        system=System.PRINCE,
        experiment_id="test_id",
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
        type=EventType.STITCH,
        src_dir_info=_SrcDirInfo(
            staging_path=None,
            local_path="test/path",
            img_count=1,
            raw_metadata={"key": "value"},
        ),
    )


async def test_import_imaging_event_successful(
    msg_kwargs: _MsgKwargs,
    uow: MockUnitOfWork,
):
    ref_id = uuid4()

    msg = ImportImagingEvent(
        ref_id=ref_id,
        **msg_kwargs.model_dump(),
    )
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
        **msg_kwargs.model_dump(),
    )
    with pytest.raises(ServiceLayerException):
        await import_imaging_event(msg, uow)
