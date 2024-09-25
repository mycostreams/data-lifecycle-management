from enum import StrEnum, auto


class System(StrEnum):
    PRINCE = auto()


class StorageSystem(StrEnum):
    STAGING = auto()


class EventType(StrEnum):
    STITCH = auto()
    VIDEO = auto()


class Algorithm(StrEnum):
    SHA256 = auto()
