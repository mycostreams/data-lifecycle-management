from functools import partial
from pathlib import Path

from prince_archiver.definitions import StorageSystem, System

from .file_system import AsyncFileSystem
from .integrations import SrcDir, SystemDir


class PathManager:
    def __init__(
        self,
        data_dir: Path,
        *,
        file_system: AsyncFileSystem | None = None,
    ):
        self.data_dir: Path = data_dir
        self.file_system = file_system or AsyncFileSystem()

    def get_staging_path(self) -> Path:
        return self.data_dir / StorageSystem.STAGING

    def get_src_dir(self, system: System | StorageSystem, path: Path) -> SrcDir:
        return SrcDir(self.data_dir / system / path, self.file_system)

    def get_system_dirs(self) -> list[SystemDir]:
        factory = partial(SystemDir, file_system=self.file_system)
        filtered_dirs = filter(
            lambda path: path.name in System,
            self.data_dir.iterdir(),
        )
        return [factory(System(path.name), path) for path in filtered_dirs]
