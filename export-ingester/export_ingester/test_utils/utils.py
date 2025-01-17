from datetime import timedelta
from typing import Callable, Generator, Iterable, TypeVar
from uuid import uuid4

from export_ingester.api_client.models import (
    ArchiveMember,
    ArchiveModel,
    EventType,
    ExportModel,
)
from export_ingester.utils import now

from .models import PaginationParams

T = TypeVar("T")


def filter_data(
    data: list[T],
    filters: list[Callable[[T], bool]],
    pagination_params: PaginationParams,
) -> tuple[int, list[T]]:
    filtered_data: Iterable[T] = data
    for filter_ in filters:
        filtered_data = filter(filter_, filtered_data)

    filtered_data = list(filtered_data)

    count = len(filtered_data)
    data = filtered_data[
        pagination_params.offset : pagination_params.offset + pagination_params.limit
    ]

    return count, data


def create_archive_data(count: int = 30) -> Generator[ArchiveModel, None, None]:
    now_ = now()
    for index in range(1, count):
        src_timestamp = now_ - timedelta(days=1)
        yield ArchiveModel(
            id=uuid4(),
            experiment_id="test",
            path=f"/test/{index:02}.tar",
            created_at=src_timestamp,
            members=[
                ArchiveMember(
                    ref_id=uuid4(),
                    timestamp=src_timestamp,
                    checksum=uuid4().hex,
                    size=1,
                    member_key="test",
                )
            ],
        )


def create_export_data(count: int = 500) -> Generator[ExportModel, None, None]:
    now_ = now()
    for index in range(1, count):
        src_timestamp = now_ - timedelta(hours=index)
        yield ExportModel(
            type=EventType.STITCH,
            experiment_id="test",
            ref_id=uuid4(),
            url="http://test.com",
            uploaded_at=src_timestamp,
            timestamp=src_timestamp,
        )
