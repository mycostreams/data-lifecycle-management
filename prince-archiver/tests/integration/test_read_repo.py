from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.adapters.repository import ReadRepo
from prince_archiver.definitions import EventType

pytestmark = pytest.mark.integration


@pytest.fixture()
def repo(session: AsyncSession) -> ReadRepo:
    return ReadRepo(session)


@pytest.mark.parametrize(
    "start,expected_count",
    ((datetime(1900, 1, 1), 1), (datetime(2010, 1, 1), 0)),
)
@pytest.mark.usefixtures("seed_data")
async def test_export_filters_by_time_range(
    repo: ReadRepo,
    start: datetime,
    expected_count: int,
):
    result = await repo.get_exports(
        start=start,
        end=datetime(2100, 1, 1),
        event_type=EventType.STITCH,
    )
    assert len(result) == expected_count


@pytest.mark.parametrize(
    "event_type,expected_count",
    ((EventType.STITCH, 1), (EventType.VIDEO, 0)),
)
@pytest.mark.usefixtures("seed_data")
async def test_export_filters_on_event_type(
    repo: ReadRepo,
    event_type: EventType,
    expected_count: int,
):
    result = await repo.get_exports(
        start=datetime(1900, 1, 1),
        end=datetime(2100, 1, 1),
        event_type=event_type,
    )
    assert len(result) == expected_count
