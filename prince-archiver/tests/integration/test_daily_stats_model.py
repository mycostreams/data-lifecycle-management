from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.models.read import DailyStats

pytestmark = pytest.mark.integration


@pytest.mark.usefixtures("seed_data")
async def test_model_contruction(session: AsyncSession):
    result = await session.scalars(select(DailyStats))
    entries = result.all()

    assert len(entries) == 3

    first, second, third = sorted(entries, key=lambda item: item.date)

    assert first.date == date(2000, 1, 1)
    assert first.event_count == 1
    assert first.export_count == 0
    assert first.archive_count == 0

    assert second.date == date(2001, 1, 1)
    assert second.event_count == 0
    assert second.export_count == 1
    assert second.archive_count == 0

    assert third.date == date(2002, 1, 1)
    assert third.event_count == 0
    assert third.export_count == 0
    assert third.archive_count == 1
