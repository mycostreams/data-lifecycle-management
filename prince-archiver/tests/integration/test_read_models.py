from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.definitions import EventType
from prince_archiver.models.read import Archive, ArchiveMember, DailyStats, Export


@pytest.mark.usefixtures("seed_data")
async def test_export_model(session: AsyncSession):
    result = await session.scalar(select(Export))

    assert result

    assert result.ref_id == UUID("0b036a6a5ba745aea24290106014b08d")
    assert result.type == EventType.STITCH
    assert result.timestamp == datetime(2000, 1, 1, tzinfo=UTC)
    assert result.uploaded_at == datetime(2001, 1, 1, tzinfo=UTC)
    assert result.key == "test/key"


@pytest.mark.usefixtures("seed_data")
async def test_data_archive_entry_model(session: AsyncSession):
    result = await session.scalar(select(Archive))

    assert result

    assert result.id == UUID("611598397745466bb78b82f4c462fd6a")
    assert result.path == "images/test_experiment_id/test.tar"
    assert result.type == EventType.STITCH
    assert result.created_at == datetime(2002, 1, 1, tzinfo=UTC)
    assert result.member_count == 1
    assert result.experiment_id == "test_experiment_id"


@pytest.mark.usefixtures("seed_data")
async def test_data_archive_member_model(session: AsyncSession):
    result = await session.scalar(select(ArchiveMember))

    assert result
    assert result.id == UUID("a9d959f074dd4f22b037c402372a0bbc")
    assert result.data_archive_entry_id == UUID("611598397745466bb78b82f4c462fd6a")
    assert result.ref_id == UUID("0b036a6a5ba745aea24290106014b08d")
    assert result.member_key == "test_member_key"
    assert result.timestamp == datetime(2000, 1, 1, tzinfo=UTC)
    assert result.type == EventType.STITCH
    assert result.size == 10
    assert result.checksum == "test_hex"


@pytest.mark.usefixtures("seed_data")
async def test_daily_stats_model(session: AsyncSession):
    result = await session.scalar(select(DailyStats))

    assert result
    assert result.date == date(2000, 1, 1)
    assert result.event_count == 1
    assert result.export_count == 1
    assert result.archive_count == 1
