from pathlib import Path

from prince_archiver.definitions import System

from .file_system import AsyncFileSystem
from .integrations import SrcDir


class PathManager:
    def __init__(
        self,
        data_dir: Path,
        *,
        file_system: AsyncFileSystem | None = None,
    ):
        self.data_dir: Path = data_dir
        self.file_system = file_system or AsyncFileSystem()

    def get_src_dir(self, system: System, path: Path) -> SrcDir:
        return SrcDir(self.data_dir / system / path, self.file_system)
