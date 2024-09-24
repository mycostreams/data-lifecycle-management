import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory
from typing import AsyncGenerator, Generator, Optional

from s3fs import S3FileSystem
from s3fs.core import version_id_kw

from .definitions import Mode
from .utils import DateT


@asynccontextmanager
async def managed_s3_file_system() -> AsyncGenerator[S3FileSystem, None]:
    s3 = S3FileSystem(asynchronous=True)

    session = await s3.set_session()

    yield s3

    await session.close()


class ExperimentFileSystem:
    def __init__(
        self,
        s3: S3FileSystem,
        bucket_name: str,
    ):
        self.s3 = s3
        self.bucket_name = bucket_name
        self.batch_size = -1

    async def list_files_by_date(
        self,
        date: DateT,
        mode: Optional[Mode] = None,
    ) -> dict[str, list[str]]:
        date_prefix = date.strftime("%Y%m%d")

        files = await self.s3._glob(
            f"{self.bucket_name}/{mode}/*/{date_prefix}*.tar",
        )
        return self._group_files(files)

    async def get_files(self, files: list[str], target_dir: Path):
        await self.s3._get(files, f"{target_dir}/", batch_size=self.batch_size)

    async def tag(self, path: str, *, _tags: Optional[dict[str, str]] = None):
        tags = _tags or {"archived": "true"}
        tag = {"TagSet": [{"Key": k, "Value": v} for k, v in tags.items()]}

        bucket, key, version_id = self.s3.split_path(path)

        await self.s3._call_s3(
            "put_object_tagging",
            Bucket=bucket,
            Key=key,
            Tagging=tag,
            **version_id_kw(version_id),
        )

    @staticmethod
    def _group_files(files: list[str]) -> dict[str, list[str]]:
        data: dict[str, list[str]] = defaultdict(list)
        for file_obj, file in zip(map(Path, files), files):
            data[file_obj.parent.name].append(file)
        return data


class _TempDir:
    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self) -> Path:
        return self._path


class ArchiveFileSystem:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.pool = None

    def exists(self, path: Path) -> bool:
        return (self.base_path / path).exists()

    async def add(self, temp_dir: _TempDir, target: Path):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.pool, self._add, temp_dir, target)

    def _add(self, temp_dir: _TempDir, target: Path):
        target = self.base_path / target
        target.parent.mkdir(parents=True, exist_ok=True)
        with TarFile.open(target, "w") as tar:
            tar.add(temp_dir.path, arcname=".")

    @staticmethod
    @contextmanager
    def get_temp_dir() -> Generator[_TempDir, None, None]:
        with TemporaryDirectory() as _temp_path:
            yield _TempDir(Path(_temp_path))
