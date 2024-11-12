"""Definition of value objects."""

from dataclasses import dataclass

from prince_archiver.definitions import Algorithm


@dataclass
class Checksum:
    hex: str
    algorithm: Algorithm = Algorithm.SHA256
