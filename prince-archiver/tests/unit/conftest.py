from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from prince_archiver.definitions import EventType
from prince_archiver.domain.models import EventArchive, ImagingEvent
from prince_archiver.domain.value_objects import Checksum
from prince_archiver.models import DataArchiveEntry, ObjectStoreEntry, Timestep


@pytest.fixture(name="archived_timestep")
def fixture_archived_timestep() -> Timestep:
    return Timestep(
        object_store_entry=ObjectStoreEntry(key="test/a"),
        data_archive_entry=DataArchiveEntry(),
    )


@pytest.fixture(name="unarchived_timestep")
def unarchived_timestep() -> Timestep:
    return Timestep(
        object_store_entry=ObjectStoreEntry(key="test/b"),
    )


@pytest.fixture(name="unexported_imaging_event")
def fixture_unexported_imaging_event() -> ImagingEvent:
    return ImagingEvent.factory(
        ref_id=uuid4(),
        type=EventType.STITCH,
        experiment_id="test_experiment_id",
        local_path=Path("unexported/path"),
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
    )


@pytest.fixture(name="exported_imaging_event")
def fixture_exported_imaging_event() -> ImagingEvent:
    imaging_event = ImagingEvent.factory(
        ref_id=uuid4(),
        type=EventType.STITCH,
        experiment_id="test_experiment_id",
        local_path=Path("exported/path"),
        timestamp=datetime(2001, 1, 1, tzinfo=UTC),
    )

    imaging_event.add_event_archive(
        EventArchive(
            id=uuid4(),
            size=10,
            checksum=Checksum(hex="321"),
        )
    )

    return imaging_event
