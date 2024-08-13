import asyncio
import logging
from concurrent.futures import Executor
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

import s3fs
from aiofiles.tempfile import TemporaryDirectory

from prince_archiver.file import tar
from prince_archiver.models import ObjectStoreEntry
from prince_archiver.service_layer.messagebus import AbstractHandler
from prince_archiver.service_layer.uow import AbstractUnitOfWork

from .dto import UploadDTO

LOGGER = logging.getLogger(__name__)


class UploadHandler(AbstractHandler[UploadDTO]):
    def __init__(
        self,
        s3: s3fs.S3FileSystem,
        pool: Executor | None = None,
    ):
        self.s3 = s3
        self.pool = pool

    async def __call__(self, message: UploadDTO, uow: AbstractUnitOfWork):
        async with (
            uow,
            self.get_temp_archive(message) as temp_archive_path,
        ):
            LOGGER.info("Uploading %s", message.key)
            await self.s3._put_file(temp_archive_path, message.key)
            await uow.commit()

    @asynccontextmanager
    async def get_temp_archive(
        self,
        message: UploadDTO,
    ) -> AsyncGenerator[Path, None]:
        LOGGER.info("Creating temp archive %s", message.key)

        async with AsyncExitStack() as stack:
            temp_dir = await stack.enter_async_context(TemporaryDirectory())
            temp_archive_path = Path(temp_dir, f"{uuid4().hex[:4]}.tar")

            await self._tar_img_folder(message.img_dir, temp_archive_path)

            yield temp_archive_path

    async def _tar_img_folder(self, src_dir: Path, target_path: Path):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.pool, tar, src_dir, target_path)


async def add_upload_to_db(
    message: UploadDTO,
    uow: AbstractUnitOfWork,
):
    LOGGER.info("Adding object store db entry %s", message.key)
    async with uow:
        if timestep := await uow.timestamps.get(id=message.timestep_id):
            if not timestep.object_store_entry:
                timestep.object_store_entry = ObjectStoreEntry(key=message.key)

        await uow.commit()
