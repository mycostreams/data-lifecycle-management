import asyncio
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import aiofiles
import aiofiles.os
import s3fs
from aiofiles.tempfile import TemporaryDirectory

from prince_archiver.db import AbstractUnitOfWork
from prince_archiver.dto import TimestepDTO
from prince_archiver.file import acompress, atar
from prince_archiver.messagebus import AbstractHandler
from prince_archiver.models import ObjectStoreEntry

from .dto import Upload

LOGGER = logging.getLogger(__name__)


class UploadHandler(AbstractHandler[TimestepDTO]):

    def __init__(
        self,
        s3: s3fs.S3FileSystem,
        bucket_name: str,
        pool,
        base_dir: Path,
    ):
        self.s3 = s3
        self.bucket_name = bucket_name
        self.pool = pool
        self.base_dir = base_dir

    async def __call__(self, message: TimestepDTO, uow: AbstractUnitOfWork):
        async with (
            uow,
            self.get_temp_archive(message) as temp_archive_path,
        ):
            await self.s3._put_file(
                temp_archive_path,
                f"{self.bucket_name}/{message.key}",
            )

            uow.add_message(
                Upload(
                    timestep_id=message.timestep_id,
                    bucket=self.bucket_name,
                    key=message.key,
                )
            )
            await uow.commit()

    @asynccontextmanager
    async def get_temp_archive(
        self, message: TimestepDTO
    ) -> AsyncGenerator[Path, None]:
        src_dir = self.base_dir / message.timestep_dir_name / message.img_dir_name

        async with AsyncExitStack() as stack:
            temp_dirs = await asyncio.gather(
                *(stack.enter_async_context(TemporaryDirectory()) for _ in range(2)),
            )
            temp_img_dir, temp_archive_dir = map(Path, temp_dirs)
            temp_archive_path = temp_archive_dir / message.archive_name

            await self._compress_img_folder(src_dir, temp_img_dir)
            await self._tar_img_folder(temp_img_dir, temp_archive_path)

            yield temp_archive_path

    async def _compress_img_folder(self, src_dir: Path, target_dir: Path):
        src_files = map(lambda path: src_dir / path, await aiofiles.os.listdir(src_dir))
        await asyncio.gather(
            *(acompress(file, target_dir / file.name, self.pool) for file in src_files),
        )

    async def _tar_img_folder(self, src_dir: Path, target_path: Path):
        await atar(src_dir, target_path, self.pool)


async def add_upload_to_db(
    message: Upload,
    uow: AbstractUnitOfWork,
):
    async with uow:
        if timestep := await uow.timestamps.get(id=message.timestep_id):
            timestep.object_store_entry = ObjectStoreEntry(
                **message.model_dump(exclude={"timestep_id"})
            )
        await uow.commit()
