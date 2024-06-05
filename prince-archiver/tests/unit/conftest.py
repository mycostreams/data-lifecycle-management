import pytest

from prince_archiver.models import DataArchiveEntry, ObjectStoreEntry, Timestep


@pytest.fixture(name="archived_timestep")
def fixture_archived_timestep() -> Timestep:
    return Timestep(
        object_store_entry=ObjectStoreEntry(bucket="test", key="a"),
        data_archive_entry=DataArchiveEntry(),
    )


@pytest.fixture(name="unarchived_timestep")
def unarchived_timestep() -> Timestep:
    return Timestep(
        object_store_entry=ObjectStoreEntry(bucket="test", key="b"),
    )
