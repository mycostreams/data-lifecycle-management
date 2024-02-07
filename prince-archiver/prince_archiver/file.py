from abc import ABC, abstractmethod
from hashlib import file_digest
from pathlib import Path
from shutil import make_archive


class AbstractFile(ABC):

    @property
    @abstractmethod
    def path(self) -> Path: ...

    @abstractmethod
    def get_checksum(self) -> str: ...


class AbstractFileSystem(ABC):

    @abstractmethod
    def make_archive(self, source: Path, target: Path) -> AbstractFile: ...


class File(AbstractFile):

    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self):
        return self._path

    def get_checksum(self) -> str:
        with self._path.open("rb") as file:
            return file_digest(file, "sha256").hexdigest()


class FileSystem:

    def make_archive(self, source: Path, target: Path) -> File:

        make_archive(
            base_name=str(target.parent / target.stem),
            format=target.suffix.strip("."),
            root_dir=source.parent,
            base_dir=source.name,
        )

        return File(path=target)
