from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.db import TimestepRepo
from prince_archiver.models import ObjectStoreEntry, Timestep

pytestmark = pytest.mark.integration


@pytest.fixture(name="timestep")
async def fixture_timestep() -> Timestep:
    return Timestep(
        timestep_id=UUID("8d2b1f49f5af4b6b853173e9ae9ef3b3"),
        experiment_id="test-experiment-id",
        position=1,
        img_count=150,
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
        local_dir=None,
        object_store_entry=ObjectStoreEntry(
            key="test-key",
            bucket="test-bucket",
            created_at=datetime(2010, 1, 1, tzinfo=UTC),
        ),
    )


@pytest.fixture(name="repo")
async def fixture_repo(timestep: Timestep, session: AsyncSession) -> TimestepRepo:
    # Populate the db
    session.add(timestep)
    await session.commit()

    return TimestepRepo(session)


async def test_get_by_date(repo: TimestepRepo):
    # Invalid
    assert not await repo.get_by_date(date.today())

    # Valid
    timesteps = await repo.get_by_date(date(2000, 1, 1))
    assert len(timesteps) == 1


async def test_get_by_id(repo: TimestepRepo):
    # Invalid id
    assert not await repo.get(uuid4())

    # Valid id
    timestep = await repo.get(UUID("8d2b1f49f5af4b6b853173e9ae9ef3b3"))
    assert timestep
