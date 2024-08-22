from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.adapters.repository import ImagingEventRepo
from prince_archiver.definitions import EventType
from prince_archiver.domain.models import ImagingEvent

pytestmark = pytest.mark.integration


@pytest.fixture()
def repo(session: AsyncSession) -> ImagingEventRepo:
    return ImagingEventRepo(session)


async def test_add(repo: ImagingEventRepo):
    stitch_event = ImagingEvent.factory(
        ref_id=uuid4(),
        experiment_id="experiment_id",
        local_path=Path("test/path/"),
        timestamp=datetime.now(),
        type=EventType.STITCH,
    )

    cached_id = stitch_event.id

    repo.add(stitch_event)
    await repo.session.commit()

    # Check that expected models are populated
    stmt = text("SELECT * FROM imaging_events WHERE id=:id")
    result = await repo.session.execute(stmt.bindparams(id=cached_id.hex))
    assert len(result.all()) == 1


@pytest.mark.usefixtures("seed_data")
async def test_get_by_ref_date(repo: ImagingEventRepo):
    # Test an invallid date
    assert not await repo.get_by_ref_date(date.today())

    imaging_events = await repo.get_by_ref_date(date(2000, 1, 1))
    assert imaging_events


@pytest.mark.usefixtures("seed_data")
async def test_get_by_ref_id(repo: ImagingEventRepo):
    # Test an invalid ref id
    assert not await repo.get_by_ref_id(uuid4())

    imaging_events = await repo.get_by_ref_id(UUID("0b036a6a5ba745aea24290106014b08d"))
    assert imaging_events
