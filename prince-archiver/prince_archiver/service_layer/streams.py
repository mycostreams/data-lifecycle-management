import logging
from enum import StrEnum, auto

from pydantic import TypeAdapter, ValidationError

from prince_archiver.adapters.streams import (
    AbstractIncomingMessage,
    AbstractOutgoingMessage,
)

from .exceptions import InvalidStreamMessage
from .messages import ExportedImagingEvent, ImagingEventStream

LOGGER = logging.getLogger(__name__)


class Streams(StrEnum):
    new_imaging_event = "data-ingester:new-imaging-event"
    status_update = "state-manager:status-update"


class Group(StrEnum):
    export_event = auto()
    import_event = auto()


MetadataModel = TypeAdapter(dict)


class Message(AbstractOutgoingMessage):
    def __init__(self, data: ImagingEventStream):
        self.data = data

    def fields(self) -> dict:
        return {
            **self.data.model_dump(mode="json", exclude={"raw_metadata"}),
            "metadata": MetadataModel.dump_json(self.data.raw_metadata),
        }


class IncomingMessage(AbstractIncomingMessage[ImagingEventStream]):
    def processed_data(self) -> ImagingEventStream:
        try:
            return ImagingEventStream(
                **{k.decode(): v.decode() for k, v in self.raw_data.items()},
                raw_metadata=MetadataModel.validate_json(
                    self.raw_data.get(b"metadata", b"{}"),
                ),
            )
        except ValidationError as exc:
            raise InvalidStreamMessage("Invalid message") from exc


class OutgoingExportMessage(AbstractOutgoingMessage):
    def __init__(self, data: ExportedImagingEvent):
        self.data = data

    def fields(self) -> dict:
        return self.data.model_dump(mode="json")


class IncomingExportMessage(AbstractIncomingMessage[ExportedImagingEvent]):
    def processed_data(self) -> ExportedImagingEvent:
        try:
            return ExportedImagingEvent(
                **{k.decode(): v.decode() for k, v in self.raw_data.items()}
            )
        except ValidationError as exc:
            raise InvalidStreamMessage("Invalid message") from exc
