from datetime import date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.db import ImagingEventRepo
from prince_archiver.definitions import System
from prince_archiver.domain.models import StitchEvent, StitchParams
from prince_archiver.domain.value_objects import GridSize, Location

pytestmark = pytest.mark.integration


@pytest.fixture()
def repo(session: AsyncSession) -> ImagingEventRepo:
    return ImagingEventRepo(session)


async def test_add(repo: ImagingEventRepo):
    stitch_event = StitchEvent.factory(
        ref_id=uuid4(),
        experiment_id="experiment_id",
        local_path="/test/path/",
        timestamp=datetime.now(),
        location=Location(system=System.PRINCE, position=3),
        params=StitchParams(grid_size=GridSize(10, 10)),
    )
    id = stitch_event.id

    repo.add(stitch_event)
    await repo.session.commit()

    # Check that expected models are populated
    stmt = text("SELECT * FROM imaging_events WHERE id=:id")
    result = await repo.session.execute(stmt.bindparams(id=id.hex))
    assert len(result.all()) == 1

    stmt = text("SELECT * FROM stitch_params WHERE imaging_event_id=:id")
    result = await repo.session.execute(stmt.bindparams(id=id.hex))


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
