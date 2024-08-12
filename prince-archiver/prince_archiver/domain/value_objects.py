"""Definition of value objects."""

from dataclasses import dataclass

from prince_archiver.definitions import Algorithm, System


@dataclass
class Checksum:
    hex: str
    algorithm: Algorithm = Algorithm.SHA256


@dataclass
class Location:
    system: System
    position: int


@dataclass
class FrameSize:
    row: int
    col: int


@dataclass
class GridSize:
    row: int
    col: int
