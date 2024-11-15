import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator

from prince_archiver.definitions import System
from prince_archiver.domain.value_objects import Checksum

from .file_system import AsyncFileSystem, MetaData


class SystemDir:
    def __init__(
        self,
        system: System,
        path: Path,
        file_system: AsyncFileSystem,
    ):
        self.system = system
        self.path = path.absolute()
        self.file_system = file_system

    def get_src_dir(self, relative_path: Path) -> "SrcDir":
        return SrcDir(
            path=self.path / relative_path,
            file_system=self.file_system,
        )

    def is_relative(self, path: Path) -> bool:
        try:
            path.absolute().relative_to(self.path.absolute())
        except ValueError:
            return False
        return True


class SrcDir:
    def __init__(
        self,
        path: Path,
        file_system: AsyncFileSystem,
    ):
        self.path = path.absolute()
        self.file_system = file_system

    async def exists(self) -> bool:
        return await self.file_system.exists(self.path)

    async def copy(self, target_dir: Path):
        await self.file_system.copy_tree(self.path, target_dir)

    async def rm(self):
        await self.file_system.rm_tree(self.path)

    @asynccontextmanager
    async def get_temp_archive(
        self,
        *,
        metadata: MetaData | None = None,
    ) -> AsyncGenerator["ArchiveFile", None]:
        temp_archive = self.file_system.get_temp_archive(self.path, metadata=metadata)
        async with temp_archive as path:
            yield ArchiveFile(path, self.file_system)


@dataclass
class ArchiveInfo:
    checksum: Checksum
    size: int


class ArchiveFile:
    DEFAULT_CHUNK_SIZE = 10 * 1024

    def __init__(
        self,
        path: Path,
        file_system: AsyncFileSystem,
    ):
        self.path = path
        self.file_system = file_system

    async def get_checksum(self, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Checksum:
        return await self.file_system.get_checksum(self.path, chunk_size)

    async def get_size(self) -> int:
        return await self.file_system.get_size(self.path)

    async def get_info(self) -> ArchiveInfo:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(self.get_checksum())
            t2 = tg.create_task(self.get_size())

        return ArchiveInfo(
            checksum=t1.result(),
            size=t2.result(),
        )
