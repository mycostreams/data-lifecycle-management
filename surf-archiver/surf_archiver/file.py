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
        mode: Mode = Mode.STITCH,
    ) -> dict[str, list[str]]:
        files = await self.s3._glob(
            f"{self.bucket_name}/{mode.value}/*/*/*.tar",
        )
        untagged_files = []
        for file in files:
            if not await self._has_tag(file, "archived", "true"):
                untagged_files.append(file)
        return self._group_files(untagged_files)

    async def _has_tag(self, file: str, tag_key: str, tag_value: str) -> bool:
        """
        Check if the file has the given tag by using the S3 API to fetch tags.
        """
        bucket, key, version_id = self.s3.split_path(file)

        # Fetch tags for the object
        response = await self.s3._call_s3(
            "get_object_tagging",
            Bucket=bucket,
            Key=key,
            **version_id_kw(version_id),
        )

        # Parse and check the tags
        tags = {tag["Key"]: tag["Value"] for tag in response.get("TagSet", [])}
        return tags.get(tag_key) == tag_value
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
        data: dict[(str, str), list[str]] = defaultdict(list)
        for file_obj, file in zip(map(Path, files), files):
            data[(file_obj.parent.parent.name,file_obj.parent.name)].append(file)
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
