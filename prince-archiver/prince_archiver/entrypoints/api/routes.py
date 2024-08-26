import asyncio
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from s3fs import S3FileSystem

from prince_archiver.service_layer.uow import AbstractUnitOfWork
from prince_archiver.utils import now

from .dependencies import get_file_system, get_uow
from .models import ExportModel

router = APIRouter()


@router.get(
    "/exports",
    response_model=list[ExportModel],
)
async def exports(
    uow: Annotated[AbstractUnitOfWork, Depends(get_uow)],
    file_system: Annotated[S3FileSystem, Depends(get_file_system)],
) -> list[ExportModel]:
    """Get latest exports."""
    exports = await uow.read.get_exports(
        start=now() - timedelta(hours=24),
    )

    # Need to fetch the presigned urls
    presigned_urls = await asyncio.gather(
        *(file_system._url(item.key) for item in exports),
    )

    iterator = zip(exports, presigned_urls)
    return [ExportModel(**export.__dict__, url=url) for export, url in iterator]
