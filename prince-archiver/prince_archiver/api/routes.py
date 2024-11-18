import asyncio
from functools import partial
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from s3fs import S3FileSystem
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.models import read

from .deps import get_file_system, get_session
from .models import (
    ArchiveModel,
    ArchivesModel,
    DailyStatsModel,
    ExportFilterParams,
    ExportsModel,
)
from .utils import get_pagininated_results

router = APIRouter(prefix="/api/1")


@router.get("/exports")
async def list_exports(
    filter_query: Annotated[ExportFilterParams, Query()],
    session: Annotated[AsyncSession, Depends(get_session)],
    file_system: Annotated[S3FileSystem, Depends(get_file_system)],
) -> ExportsModel:
    """Get latest exports."""
    filter_params = [
        read.Export.type == filter_query.event_type,
        read.Export.uploaded_at > filter_query.start,
        read.Export.uploaded_at < filter_query.end,
    ]

    count, exports = await get_pagininated_results(
        session=session,
        model=read.Export,
        filter_params=filter_params,
        limit=filter_query.limit,
        offset=filter_query.offset,
    )

    # Need to fetch the presigned urls
    presigned_urls = await asyncio.gather(
        *(file_system._url(item.key) for item in exports),
    )
    iterator = zip(exports, presigned_urls)

    return ExportsModel(
        count=count,
        data=[{**item.__dict__, "url": url} for item, url in iterator],
    )


@router.get("/archives")
async def list_archives(
    session: Annotated[AsyncSession, Depends(get_session)],
    experiment_id: str | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> ArchivesModel:
    filter_params = []
    if experiment_id:
        filter_params.append(
            read.Archive.experiment_id == experiment_id,
        )

    count, archives = await get_pagininated_results(
        session=session,
        model=read.Archive,
        filter_params=filter_params,
        limit=limit,
        offset=offset,
    )

    get_url = partial(router.url_path_for, "read_archive")

    return ArchivesModel(
        count=count,
        data=[{**item.__dict__, "url": get_url(id=item.id)} for item in archives],
    )


@router.get("/archives/{id}", name="read_archive")
async def read_archive(
    id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ArchiveModel:
    archive = await session.scalar(select(read.Archive).where(read.Archive.id == id))
    if not archive:
        raise HTTPException(status_code=404, detail="item not found")

    members = await session.scalars(
        select(read.ArchiveMember).where(read.ArchiveMember.data_archive_entry_id == id)
    )

    return ArchiveModel(
        **archive.__dict__,
        members=[item.__dict__ for item in members.all()],
    )


@router.get("/daily-stats")
async def list_daily_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[DailyStatsModel]:
    result = await session.scalars(
        select(read.DailyStats).order_by(read.DailyStats.date.desc()).limit(7)
    )
    return [DailyStatsModel(**item.__dict__) for item in result.all()]
