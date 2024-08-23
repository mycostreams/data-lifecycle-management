from datetime import date
from typing import Generator, Mapping
from uuid import UUID

from pydantic import BaseModel

from prince_archiver.adapters.repository import (
    AbstractDataArchiveEntryRepo,
    AbstractImagingEventRepo,
)
from prince_archiver.domain.models import DataArchiveEntry, ImagingEvent
from prince_archiver.service_layer.uow import AbstractUnitOfWork


class MockDataArchiveEntryRepo(AbstractDataArchiveEntryRepo):
    def __init__(
        self,
        data_archive_entries: list[DataArchiveEntry] | None = None,
    ):
        self.entries: list[DataArchiveEntry] = data_archive_entries or []

    def add(self, data_archive_entry: DataArchiveEntry) -> None:
        self.entries.append(data_archive_entry)

    async def get_by_path(self, path: str) -> DataArchiveEntry | None:
        return self._mapping.get(path)

    @property
    def _mapping(self) -> Mapping[str, DataArchiveEntry]:
        return {item.path: item for item in self.entries}


class MockImagingEventRepo(AbstractImagingEventRepo):
    def __init__(
        self,
        imaging_events: list[ImagingEvent] | None = None,
    ):
        self.entries: list[ImagingEvent] = imaging_events or []

    def add(self, image_event: ImagingEvent) -> None:
        self.entries.append(image_event)

    async def get_by_ref_id(self, event_id: UUID) -> ImagingEvent | None:
        return self._mapping.get(event_id)

    async def get_by_ref_date(self, date: date) -> list[ImagingEvent]:
        filtered_results = filter(
            lambda item: item.timestamp.date() == date,
            self.entries,
        )
        return list(filtered_results)

    @property
    def _mapping(self) -> Mapping[UUID, ImagingEvent]:
        return {item.ref_id: item for item in self.entries}


class MockUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        imaging_event_repo: MockImagingEventRepo | None = None,
        data_archive_repo: MockDataArchiveEntryRepo | None = None,
    ):
        self.imaging_events: MockImagingEventRepo = (
            imaging_event_repo or MockImagingEventRepo()
        )
        self.data_archive: MockDataArchiveEntryRepo = (
            data_archive_repo or MockDataArchiveEntryRepo()
        )

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
