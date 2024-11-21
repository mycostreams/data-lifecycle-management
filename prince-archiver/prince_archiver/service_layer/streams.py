import logging
from enum import StrEnum, auto

from pydantic import ValidationError

from prince_archiver.adapters.streams import (
    AbstractIncomingMessage,
    AbstractOutgoingMessage,
)

from .dto import ExportedImagingEvent, NewImagingEvent
from .exceptions import InvalidStreamMessage

LOGGER = logging.getLogger(__name__)


class Streams(StrEnum):
    imaging_events = "dlm:imaging-events"
    upload_events = "dlm:export-events"


class Group(StrEnum):
    upload_worker = auto()
    state_manager = auto()


class Message(AbstractOutgoingMessage):
    def __init__(self, data: NewImagingEvent):
        self.data = data

    def fields(self) -> dict:
        return self.data.model_dump(mode="json", round_trip=True)


class IncomingMessage(AbstractIncomingMessage[NewImagingEvent]):
    def processed_data(self) -> NewImagingEvent:
        try:
            return NewImagingEvent(
                **{k.decode(): v.decode() for k, v in self.raw_data.items()},
            )
        except ValidationError as exc:
            raise InvalidStreamMessage("Invalid message") from exc


class OutgoingExportMessage(AbstractOutgoingMessage):
    def __init__(self, data: ExportedImagingEvent):
        self.data = data

    def fields(self) -> dict:
        return self.data.model_dump(mode="json", round_trip=True)


class IncomingExportMessage(AbstractIncomingMessage[ExportedImagingEvent]):
    def processed_data(self) -> ExportedImagingEvent:
        try:
            return ExportedImagingEvent(
                **{k.decode(): v.decode() for k, v in self.raw_data.items()}
            )
        except ValidationError as exc:
            raise InvalidStreamMessage("Invalid message") from exc
