from functools import partial
from pathlib import Path
from typing import Protocol

from prince_archiver.definitions import SrcDirKey, System

from .file_system import AsyncFileSystem
from .integrations import SrcDir, SystemDir


class PathSettings(Protocol):
    STAGING_DIR: Path | None
    PRINCE_SRC_DIR: Path


class PathManager:
    def __init__(
        self,
        path_mapping: dict[SrcDirKey, Path],
        *,
        file_system: AsyncFileSystem | None = None,
    ):
        self.mapping = path_mapping
        self.file_system = file_system or AsyncFileSystem()

    def get_src_dir(self, key: SrcDirKey | System, path: Path) -> SrcDir:
        return SrcDir(self.mapping[SrcDirKey[key.name]] / path, self.file_system)

    def get_system_dirs(self) -> list[SystemDir]:
        args = [(key, self.mapping.get(SrcDirKey[key.name])) for key in System]
        factory = partial(SystemDir, file_system=self.file_system)
        return [factory(system, path) for system, path in args if path]

    @classmethod
    def from_settings(cls, settings: PathSettings):
        mapping = {
            SrcDirKey.STAGING: settings.STAGING_DIR,
            SrcDirKey.PRINCE: settings.PRINCE_SRC_DIR,
        }
        return cls({k: v for k, v in mapping.items() if v})
