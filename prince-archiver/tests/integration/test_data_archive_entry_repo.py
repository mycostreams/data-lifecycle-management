from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.adapters.repository import DataArchiveEntryRepo
from prince_archiver.domain.models import DataArchiveEntry

pytestmark = pytest.mark.integration


@pytest.fixture()
def repo(session: AsyncSession) -> DataArchiveEntryRepo:
    return DataArchiveEntryRepo(session)


async def test_add(repo: DataArchiveEntryRepo):
    ref_id = uuid4()

    data_archive_entry = DataArchiveEntry(
        id=ref_id,
        job_id=None,
        path="test_path",
    )

    repo.add(data_archive_entry)

    await repo.session.commit()

    stmt = text("SELECT * FROM data_archive_entries WHERE id=:id")
    result = await repo.session.execute(stmt.bindparams(id=ref_id.hex))
    assert len(result.all()) == 1


@pytest.mark.usefixtures("seed_data")
async def test_get_by_path(repo: DataArchiveEntryRepo):
    # Test an invalid path
    assert not await repo.get_by_path("nonexistent/path")

    # test with valid path
    data_archive_entry = await repo.get_by_path("images/test_experiment_id/test.tar")
    assert data_archive_entry
