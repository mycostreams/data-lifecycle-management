from enum import StrEnum, auto


class System(StrEnum):
    PRINCE = auto()
    TSU_EXP002 = "tsu-exp002"
    TSU_EXP003 = "tsu-exp003"


class EventType(StrEnum):
    STITCH = auto()
    VIDEO = auto()


class Algorithm(StrEnum):
    SHA256 = auto()
