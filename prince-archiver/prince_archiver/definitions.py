from enum import StrEnum, auto


class System(StrEnum):
    PRINCE = auto()


class SrcDirKey(StrEnum):
    PRINCE = auto()
    STAGING = auto()


class EventType(StrEnum):
    STITCH = auto()
    VIDEO = auto()


class Algorithm(StrEnum):
    SHA256 = auto()
