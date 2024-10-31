import logging
from enum import StrEnum, auto

from pydantic import TypeAdapter

from prince_archiver.adapters.streams import AbstractIncomingMessage, AbstractMessage

from .messages import ImagingEventStream

LOGGER = logging.getLogger(__name__)


class Streams(StrEnum):
    new_imaging_event = "data-ingester:new-imaging-event"


class Group(StrEnum):
    export_event = auto()
    import_event = auto()


MetadataModel = TypeAdapter(dict)


class Message(AbstractMessage):
    def __init__(self, data: ImagingEventStream):
        self.data = data

    def fields(self) -> dict:
        return {
            **self.data.model_dump(mode="json", exclude={"raw_metadata"}),
            "metadata": MetadataModel.dump_json(self.data.raw_metadata),
        }


class IncomingMessage(AbstractIncomingMessage):
    def processed_data(self) -> ImagingEventStream:
        return ImagingEventStream(
            **{k.decode(): v.decode() for k, v in self.raw_data.items()},
            raw_metadata=MetadataModel.validate_json(
                self.raw_data.get(b"metadata", b"{}"),
            ),
        )
