import tarfile
from abc import ABC, abstractmethod
from hashlib import file_digest
from pathlib import Path


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


class FileSystem(AbstractFileSystem):

    def make_archive(self, source: Path, target: Path) -> File:
        with tarfile.open(target, "w") as tar:
            tar.add(source, arcname=".")
        return File(path=target)
