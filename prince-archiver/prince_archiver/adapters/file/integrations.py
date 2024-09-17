from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncGenerator

from pydantic import Json, TypeAdapter

from prince_archiver.definitions import System
from prince_archiver.service_layer.external_dto import TimestepDTO

from .file_system import AsyncFileSystem

JsonT = TypeAdapter(Json)


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

    @property
    def events_dir(self) -> Path:
        return self.path / "events"

    def get_src_dir(self, relative_path: Path) -> "SrcDir":
        return SrcDir(path=self.path / relative_path, file_system=self.file_system)

    async def iter_events(self) -> AsyncGenerator["EventFile", None]:
        for file in await self.file_system.list_dir(self.events_dir):
            if file.suffix == ".json":
                yield EventFile(file, self, self.file_system)

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

    async def get_metadata(self, filename="metadata.json") -> Json:
        path = self.path / filename
        if await self.file_system.exists(path):
            return await self.file_system.read_json(
                path,
                mapper=JsonT.validate_json,
            )
        return {}

    async def copy(self, target_dir: Path):
        await self.file_system.copy_tree(self.path, target_dir)

    async def rm(self):
        await self.file_system.rm_tree(self.path)

    @asynccontextmanager
    async def get_temp_archive(self):
        async with self.file_system.get_temp_archive(self.path) as path:
            yield ArchiveFile(path, self.file_system)


class EventFile:
    def __init__(
        self,
        path: Path,
        system_dir: SystemDir,
        file_system: AsyncFileSystem,
    ):
        self.system_dir = system_dir
        self.path = path
        self.file_system = file_system

    @property
    def timestamp(self) -> datetime:
        timestamp = int(self.path.name.split("-")[0])
        return datetime.fromtimestamp(timestamp, tz=UTC)

    async def read(self) -> TimestepDTO:
        return await self.file_system.read_json(
            self.path,
            mapper=TimestepDTO.model_validate_json,
        )

    async def rm(self):
        await self.file_system.rm(self.path)

    @asynccontextmanager
    async def process(self, remove: bool = True):
        dto = await self.read()
        try:
            yield dto, self.system_dir.get_src_dir(dto.img_dir)
        except Exception as e:
            raise e

        if remove:
            await self.rm()


class ArchiveFile:
    DEFAULT_CHUNK_SIZE = 10 * 1024

    def __init__(
        self,
        path: Path,
        file_system: "AsyncFileSystem",
    ):
        self.path = path
        self.file_system = file_system

    async def get_checksum(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        await self.file_system.get_checksum(self.path, chunk_size)

    async def get_size(self):
        await self.file_system.get_size(self.path)
