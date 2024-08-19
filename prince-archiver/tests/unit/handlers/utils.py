from datetime import date
from typing import Generator, Mapping
from uuid import UUID

from pydantic import BaseModel

from prince_archiver.adapters.repository import AbstractImagingEventRepo
from prince_archiver.domain.models import ImagingEvent
from prince_archiver.service_layer.uow import AbstractUnitOfWork


class MockImagingEventRepo(AbstractImagingEventRepo):
    def __init__(
        self,
        imaging_events: list[ImagingEvent] | None = None,
    ):
        self.imaging_events: Mapping[UUID, ImagingEvent] = {
            item.ref_id: item for item in imaging_events or []
        }

    def add(self, image_event: ImagingEvent) -> None:
        self.imaging_events[image_event.ref_id] = image_event

    async def get_by_ref_id(self, event_id: UUID) -> ImagingEvent | None:
        return self.imaging_events.get(event_id)

    async def get_by_ref_date(self, date: date) -> list[ImagingEvent]:
        filtered_results = filter(
            lambda item: item.timestamp.date() == date, self.imaging_events.values()
        )
        return list(filtered_results)


class MockUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        imaging_event_repo: AbstractImagingEventRepo | None = None,
    ):
        self.imaging_events = imaging_event_repo or MockImagingEventRepo()
        self.messages = []
        self.is_commited = False

    def add_message(self, message: BaseModel):
        self.messages.append(message)

    async def __aenter__(self) -> AbstractUnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        return await super().__aexit__(exc_type, exc_value, exc_traceback)

    async def commit(self) -> None:
        self.is_commited = True

    async def rollback(self) -> None:
        return await super().rollback()

    def collect_messages(self) -> Generator[BaseModel, None, None]:
        yield from self.messages
