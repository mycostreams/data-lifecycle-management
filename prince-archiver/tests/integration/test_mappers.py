from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from prince_archiver.definitions import EventType, System
from prince_archiver.domain import models as domain_model
from prince_archiver.domain.value_objects import Checksum

pytestmark = pytest.mark.integration


@pytest.mark.usefixtures("seed_data")
async def test_imaging_event_mappers(session: AsyncSession):
    imaging_event = await session.scalar(
        select(domain_model.ImagingEvent).options(selectinload("*"))
    )

    assert imaging_event
    assert imaging_event.timestamp == datetime(2000, 1, 1, tzinfo=UTC)
    assert imaging_event.system == System.PRINCE
    assert imaging_event.type == EventType.STITCH
    assert imaging_event.experiment_id == "test_experiment_id"

    assert (object_store_entry := imaging_event.object_store_entry)
    assert object_store_entry.key == "test_key"
    assert object_store_entry.uploaded_at == datetime(2001, 1, 1, tzinfo=UTC)

    assert (event_archive := imaging_event.event_archive)
    assert event_archive.size == 3
    assert event_archive.checksum == Checksum(hex="test_hex")

    assert (src_dir_info := imaging_event.src_dir_info)
    assert src_dir_info.staging_path is None
    assert src_dir_info.local_path == Path("test/path/")
    assert src_dir_info.img_count == 10
    assert src_dir_info.raw_metadata == {"test_key": "test_value"}


@pytest.mark.usefixtures("seed_data")
async def test_data_archive_mappers(session: AsyncSession):
    data_archive_entry = await session.scalar(
        select(domain_model.DataArchiveEntry).options(selectinload("*"))
    )

    assert data_archive_entry
    assert data_archive_entry.path == "images/test_experiment_id/test.tar"

    assert (members := data_archive_entry.members) and len(members) == 1

    member = members[0]
    assert member.src_key == "test_key"
    assert member.member_key == "test_member_key"
