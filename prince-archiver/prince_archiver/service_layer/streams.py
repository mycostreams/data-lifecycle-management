from enum import StrEnum, auto

from prince_archiver.adapters.streams import AbstractIncomingMessage, AbstractMessage

from .messages import ImagingEventStream


class Streams(StrEnum):
    new_imaging_event = "data-ingester:new-imaging-event"


class Group(StrEnum):
    export_event = auto()
    import_event = auto()


class Message(AbstractMessage):
    def __init__(self, data: ImagingEventStream):
        self.data = data

    def fields(self) -> dict:
        return {"data": self.data.model_dump_json()}


class IncomingMessage(AbstractIncomingMessage):
    def processed_data(self) -> ImagingEventStream:
        return ImagingEventStream.model_validate_json(self.raw_data[b"data"])
