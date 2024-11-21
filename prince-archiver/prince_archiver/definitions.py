from enum import StrEnum, auto


class System(StrEnum):
    PRINCE = auto()
    ZAKYNTHOS = "zakynthos"
    TSU_EXP001 = "tsu-exp001"
    TSU_EXP002 = "tsu-exp002"


class EventType(StrEnum):
    STITCH = auto()
    VIDEO = auto()


class Algorithm(StrEnum):
    SHA256 = auto()
