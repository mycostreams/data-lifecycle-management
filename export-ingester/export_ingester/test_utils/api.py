from typing import Annotated, Callable
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query

from export_ingester.api_client.models import (
    ArchiveModel,
    ArchiveSummaryModel,
    ExportModel,
    PaginatedResponse,
)

from .models import ArchivesFilterParams, ExportsFilterParams
from .utils import (
    create_archive_data,
    create_export_data,
    filter_data,
)

EXPORT_DATA = list(create_export_data())

ARCHIVES_DATA = list(create_archive_data())


app = FastAPI()


def get_archive_url(item: ArchiveModel) -> str:
    return str(app.url_path_for("get_archive", id=item.id))


@app.get("/api/1/exports", response_model=PaginatedResponse[ExportModel])
def get_exports(filter_params: Annotated[ExportsFilterParams, Query()]) -> dict:
    filters: list[Callable[[ExportModel], bool]] = [
        lambda obj: obj.type == filter_params.event_type,
        lambda obj: obj.timestamp < filter_params.end,
        lambda obj: obj.timestamp > filter_params.start,
    ]
    count, data = filter_data(EXPORT_DATA, filters, filter_params)

    return {
        "count": count,
        "data": data,
    }


@app.get(
    "/api/1/archives",
    response_model=PaginatedResponse[ArchiveSummaryModel],
)
def get_archives(filter_params: Annotated[ArchivesFilterParams, Query()]) -> dict:
    filters: list[Callable[[ArchiveModel], bool]] = [
        lambda item: item.experiment_id == filter_params.experiment_id,
    ]
    count, data = filter_data(ARCHIVES_DATA, filters, filter_params)

    return {
        "count": count,
        "data": [{"url": get_archive_url(item), **dict(item)} for item in data],
    }


@app.get(
    "/api/1/archives/{id}",
    response_model=ArchiveModel,
)
def get_archive(id: UUID):
    for item in ARCHIVES_DATA:
        if item.id == id:
            return item
    raise HTTPException(status_code=404)
