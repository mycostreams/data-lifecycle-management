from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.adapters.repository import ReadRepo

pytestmark = pytest.mark.integration


@pytest.fixture()
def repo(session: AsyncSession) -> ReadRepo:
    return ReadRepo(session)


@pytest.mark.usefixtures("seed_data")
async def test_export_within_time_range(repo: ReadRepo):
    result = await repo.get_exports(start=datetime(1900, 1, 1))
    assert len(result) == 1


@pytest.mark.usefixtures("seed_data")
async def test_export_outside_time_range(repo: ReadRepo):
    result = await repo.get_exports(start=datetime(2010, 1, 1))
    assert len(result) == 0
