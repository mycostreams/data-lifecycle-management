from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import clear_mappers
from testcontainers.postgres import PostgresContainer

from prince_archiver.definitions import Algorithm, EventType, System
from prince_archiver.models import v2 as data_models
from prince_archiver.models.mappers import init_mappers


@pytest.fixture(name="mappers", scope="session", autouse=True)
def fixture_mappers():
    init_mappers()

    yield

    clear_mappers()


@pytest.fixture(scope="session")
def postgres():
    postgres = PostgresContainer(
        "postgres:16-alpine",
        driver="asyncpg",
    )
    postgres.start()

    yield postgres

    postgres.stop()


@pytest.fixture(name="conn")
async def fixture_conn(
    postgres: PostgresContainer,
) -> AsyncGenerator[AsyncConnection, None]:
    engine = create_async_engine(postgres.get_connection_url())
    async with engine.connect() as conn:
        await conn.run_sync(data_models.Base.metadata.create_all)

        yield conn


@pytest.fixture(name="sessionmaker")
async def fixture_sessionmaker(
    conn: AsyncConnection,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    async with conn.begin_nested() as trans:
        sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=conn,
        )

        yield sessionmaker

        await trans.rollback()


@pytest.fixture(name="session")
async def fixture_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


@pytest.fixture(name="imaging_event")
def fixture_imaging_event() -> data_models.ImagingEvent:
    return data_models.ImagingEvent(
        id=uuid4(),
        ref_id=UUID("0b036a6a5ba745aea24290106014b08d"),
        type=EventType.STITCH,
        experiment_id="test_experiment_id",
        system=System.PRINCE,
        system_position=3,
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
    )


@pytest.fixture(name="data_archive_entry")
def fixture_data_archive_entry():
    return data_models.DataArchiveEntry(
        id=UUID("611598397745466bb78b82f4c462fd6a"),
        path="images/test_experiment_id/test.tar",
    )


@pytest.fixture(name="data_archive_member")
def fixture_data_archive_member(
    data_archive_entry: data_models.DataArchiveEntry,
) -> data_models.DataArchiveMember:
    return data_models.DataArchiveMember(
        member_key="test_member_key",
        src_key="test_key",
        data_archive_entry_id=data_archive_entry.id,
        created_at=datetime(2002, 1, 1, tzinfo=UTC),
    )


@pytest.fixture(name="object_store_entry")
def fixture_object_store_entry(
    imaging_event: data_models.ImagingEvent,
) -> data_models.ObjectStoreEntry:
    return data_models.ObjectStoreEntry(
        key="test_key",
        uploaded_at=datetime(2001, 1, 1, tzinfo=UTC),
        imaging_event_id=imaging_event.id,
    )


@pytest.fixture(name="event_archive")
def fixture_event_archive(
    imaging_event: data_models.ImagingEvent,
) -> data_models.EventArchive:
    return data_models.EventArchive(
        id=uuid4(),
        size=3,
        imaging_event_id=imaging_event.id,
    )


@pytest.fixture(name="checksum")
def fixture_checksum(event_archive: data_models.EventArchive):
    return data_models.ArchiveChecksum(
        hex="test_hex",
        algorithm=Algorithm.SHA256,
        event_archive_id=event_archive.id,
    )


@pytest.fixture(name="src_dir_info")
def fixture_src_dir_info(
    imaging_event: data_models.ImagingEvent,
) -> data_models.SrcDirInfo:
    return data_models.SrcDirInfo(
        id=uuid4(),
        img_count=10,
        staging_path=None,
        local_path=Path("test/path"),
        raw_metadata={"test_key": "test_value"},
        imaging_event_id=imaging_event.id,
    )


@pytest.fixture(name="seed_data")
async def fixture_seed_data(
    data_archive_entry: data_models.DataArchiveEntry,
    imaging_event: data_models.ImagingEvent,
    data_archive_member: data_models.DataArchiveMember,
    object_store_entry: data_models.ObjectStoreEntry,
    src_dir_info: data_models.SrcDirInfo,
    event_archive: data_models.EventArchive,
    checksum: data_models.ArchiveChecksum,
    session: AsyncSession,
):
    items = [
        imaging_event,
        src_dir_info,
        event_archive,
        checksum,
        object_store_entry,
        data_archive_entry,
        data_archive_member,
    ]
    for object in items:
        session.add(object)
        await session.commit()
