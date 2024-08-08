from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from prince_archiver.definitions import EventType, System
from prince_archiver.domain import models as domain_model
from prince_archiver.domain.value_objects import Checksum, Location

pytestmark = pytest.mark.integration


@pytest.mark.usefixtures("seed_data")
async def test_mappers(session: AsyncSession):
    imaging_event = await session.scalar(
        select(domain_model.ImagingEvent).options(selectinload("*"))
    )

    assert imaging_event
    assert imaging_event.timestamp == datetime(2000, 1, 1, tzinfo=UTC)
    assert imaging_event.type == EventType.STITCH
    assert imaging_event.local_path == "/test/path/"
    assert imaging_event.experiment_id == "test_experiment_id"
    assert imaging_event.location == Location(system=System.PRINCE, position=3)

    assert (data_archive_member := imaging_event.data_archive_member)
    assert data_archive_member.key == "test_key"
    assert data_archive_member.member_key == "test_member_key"

    assert (object_store_entry := imaging_event.object_store_entry)
    assert object_store_entry.key == "test_key"
    assert object_store_entry.uploaded_at == datetime(2001, 1, 1, tzinfo=UTC)

    assert (event_archive := imaging_event.event_archive)
    assert event_archive.size == 3
    assert event_archive.img_count == 10
    assert event_archive.checksum == Checksum(hex="test_hex")
