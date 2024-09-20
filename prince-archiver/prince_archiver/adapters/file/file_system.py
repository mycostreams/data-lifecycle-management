import asyncio
import logging
import shutil
import tarfile
from concurrent.futures import Executor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Awaitable, Callable, TypeVar
from uuid import uuid4

import aiofiles.os
import aiofiles.ospath
from aiofiles.tempfile import TemporaryDirectory

from prince_archiver.domain.value_objects import Checksum

from .checksum import ChecksumFactory

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
MapperT = Callable[[bytes], T]

ChecksumFactoryT = Callable[[AsyncGenerator[bytes, None]], Awaitable[Checksum]]


class AsyncFileSystem:
    def __init__(
        self,
        executor: Executor | None = None,
        checksum_factory: ChecksumFactoryT | None = None,
    ):
        self.executor = executor
        self.checksum_factory: ChecksumFactoryT = (
            checksum_factory or ChecksumFactory.get_checksum
        )

    async def get_checksum(self, path: Path, chunk_size: int) -> Checksum:
        return await self.checksum_factory(
            self.iter_bytes(path, chunk_size),
        )

    async def copy_tree(self, src: Path, target: Path):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, shutil.copytree, src, target)

    async def rm_tree(self, src: Path) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, shutil.rmtree, src)

    async def rm(self, src: Path) -> None:
        await aiofiles.os.remove(src, executor=self.executor)

    async def exists(self, path: Path) -> bool:
        return await aiofiles.ospath.exists(path, executor=self.executor)

    async def iter_bytes(self, path: Path, chunk_size: int | None):
        async with aiofiles.open(path, "rb", executor=self.executor) as file:
            chunk_size = chunk_size if isinstance(chunk_size, int) else -1
            yield await file.read(chunk_size)

    async def list_dir(self, path: Path) -> list[Path]:
        entries = await aiofiles.os.listdir(path, executor=self.executor)
        return [path / item for item in entries]

    async def get_size(self, path: Path) -> int:
        stat = await aiofiles.os.stat(path, executor=self.executor)
        return stat.st_size

    async def read_bytes(self, path: Path) -> bytes:
        return await anext(self.iter_bytes(path, chunk_size=None))

    async def read_json(
        self,
        path: Path,
        *,
        mapper: MapperT,
    ) -> T:
        return mapper(await self.read_bytes(path))

    async def tar_tree(self, src_dir: Path, target_path: Path):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._tar, src_dir, target_path)

    @staticmethod
    def _tar(src: Path, target: Path):
        LOGGER.debug("Tarring %s", src)

        target.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(target, "a") as tar:
            tar.add(src, arcname=".")

        LOGGER.debug("Tarred %s", src)

    @asynccontextmanager
    async def get_temp_archive(
        self,
        src_path: Path,
    ) -> AsyncGenerator[Path, None]:
        async with TemporaryDirectory() as temp_dir:
            temp_archive_path = Path(temp_dir, f"{uuid4().hex[:6]}.tar")

            await self.tar_tree(src_path, temp_archive_path)

            yield Path(temp_archive_path)

    @asynccontextmanager
    async def managed_dir(self, path: Path):
        try:
            yield path
        except Exception as e:
            await self.rm_tree(path)
            raise e
