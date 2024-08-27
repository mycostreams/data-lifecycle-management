import asyncio
import json
import logging
import tarfile
from concurrent.futures import Executor
from contextlib import asynccontextmanager
from hashlib import sha256
from pathlib import Path
from typing import AsyncGenerator, Awaitable, Callable, Protocol
from uuid import uuid4

import aiofiles.os
import aiofiles.ospath
from aiofiles.tempfile import TemporaryDirectory

from prince_archiver.domain.value_objects import Algorithm, Checksum

LOGGER = logging.getLogger(__name__)


ChecksumFactoryT = Callable[[Path], Awaitable[Checksum]]


class SrcPath(Path):
    """
    Path representing unarchived source image directory.
    """


class ArchivePath(Path):
    """
    Path representing archive file.
    """


class _HashProtocol(Protocol):
    def update(self, data: bytes): ...

    def hexdigest(self) -> str: ...


class _ChecksumFactory:
    """
    Class for generating checksums.
    """

    DEFAULT_CHUNK_SIZE = 10 * 1024

    HASH_MAPPING: dict[Algorithm, Callable[[], _HashProtocol]] = {
        Algorithm.SHA256: sha256,
    }

    @classmethod
    async def get_checksum(
        cls,
        path: Path,
        *,
        algorithm: Algorithm = Algorithm.SHA256,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> Checksum:
        hash = cls.HASH_MAPPING[algorithm]()
        async with aiofiles.open(path, "rb") as file:
            while chunk := await file.read(chunk_size):
                hash.update(chunk)

        return Checksum(
            algorithm=algorithm,
            hex=hash.hexdigest(),
        )


class ArchiveFileManager:
    """
    Class for managing archive files.
    """

    METADATA_FILENAME = "metadata.json"

    def __init__(
        self,
        *,
        base_path: Path | None = None,
        executor: Executor | None = None,
        checksum_factory: ChecksumFactoryT = _ChecksumFactory.get_checksum,
    ):
        self.base_path = base_path
        self.executor = executor
        self.checksum_factory = checksum_factory

    def get_src_path(self, path: Path) -> SrcPath:
        if self.base_path:
            return SrcPath(self.base_path / path)
        raise ValueError()

    async def exists(self, path: Path) -> bool:
        return await aiofiles.ospath.exists(path, executor=self.executor)

    async def get_raw_metadata(
        self,
        src_path: SrcPath,
        *,
        filename: str | None = None,
    ) -> dict:
        """
        Get raw metadata from src directory.
        """
        metadata_path = src_path / (filename or self.METADATA_FILENAME)
        if await self.exists(metadata_path):
            async with aiofiles.open(metadata_path, executor=self.executor) as file:
                return json.loads(await file.read())
        return {}

    async def get_file_count(self, src_path: SrcPath) -> int:
        files = await aiofiles.os.listdir(src_path, executor=self.executor)
        return len(files)

    async def get_archive_size(self, archive_path: ArchivePath) -> int:
        stat = await aiofiles.os.stat(archive_path, executor=self.executor)
        return stat.st_size

    async def get_archive_checksum(self, archive_path: ArchivePath) -> Checksum:
        return await self.checksum_factory(archive_path)

    @asynccontextmanager
    async def get_temp_archive(
        self,
        src_path: SrcPath,
    ) -> AsyncGenerator[ArchivePath, None]:
        async with TemporaryDirectory() as temp_dir:
            temp_archive_path = ArchivePath(temp_dir, f"{uuid4().hex[:6]}.tar")

            await self._tar_img_folder(src_path, temp_archive_path)

            yield ArchivePath(temp_archive_path)

    async def _tar_img_folder(self, src_dir: Path, target_path: Path):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._tar, src_dir, target_path)

    @staticmethod
    def _tar(src: Path, target: Path):
        LOGGER.debug("Tarring %s", src)

        target.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(target, "a") as tar:
            tar.add(src, arcname=".")

        LOGGER.debug("Tarred %s", src)
