from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prince_archiver.db import AbstractTimestepRepo, AbstractUnitOfWork
from prince_archiver.models import ObjectStoreEntry, Timestep
from prince_archiver.upload_worker.dto import UploadDTO
from prince_archiver.upload_worker.handlers import add_upload_to_db


class TestAddUploadToDB:
    @pytest.fixture(name="message")
    def fixture_message(self) -> UploadDTO:
        return UploadDTO(
            timestep_id=uuid4(),
            img_dir=Path("test/path"),
            bucket="test-bucket",
            key="test-key",
        )

    @pytest.fixture(name="timestep")
    def fixture_timestep(self) -> Timestep:
        return Timestep()

    @pytest.fixture(name="uow")
    def fixture_uow(self, timestep: Timestep) -> AbstractTimestepRepo:
        repo = AsyncMock(AbstractTimestepRepo)
        repo.get.return_value = timestep
        return AsyncMock(AbstractUnitOfWork, timestamps=repo)

    async def test_timestep_that_isnt_uploaded(
        self,
        message: UploadDTO,
        timestep: Timestep,
        uow: AbstractUnitOfWork,
    ):
        assert not timestep.object_store_entry

        await add_upload_to_db(message, uow)

        assert timestep.object_store_entry

        uow.commit.assert_awaited_once_with()

    async def test_timestep_that_is_already_uploaded(
        self,
        message: UploadDTO,
        timestep: Timestep,
        uow: AbstractUnitOfWork,
    ):
        existing_entry = ObjectStoreEntry()
        timestep.object_store_entry = existing_entry

        await add_upload_to_db(message, uow)

        assert timestep.object_store_entry == existing_entry

        uow.commit.assert_awaited_once_with()
