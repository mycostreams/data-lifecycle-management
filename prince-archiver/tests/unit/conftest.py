from datetime import UTC, datetime
from uuid import uuid4

import pytest

from prince_archiver.definitions import System
from prince_archiver.domain.models import EventArchive, StitchEvent
from prince_archiver.domain.value_objects import Checksum, Location
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


@pytest.fixture(name="unexported_stitch_event")
def fixture_unexported_stitch_event() -> StitchEvent:
    return StitchEvent.factory(
        ref_id=uuid4(),
        experiment_id="test_experiment_id",
        local_path="unexported/path",
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
        location=Location(system=System.PRINCE, position=1),
    )


@pytest.fixture(name="exported_stitch_event")
def fixture_exported_stitch_event() -> StitchEvent:
    stitch_event = StitchEvent.factory(
        ref_id=uuid4(),
        experiment_id="test_experiment_id",
        local_path="exported/path",
        timestamp=datetime(2001, 1, 1, tzinfo=UTC),
        location=Location(system=System.PRINCE, position=1),
    )

    stitch_event.add_event_archive(
        EventArchive(
            id=uuid4(),
            size=10,
            img_count=10,
            checksum=Checksum(hex="321"),
        )
    )

    return stitch_event
