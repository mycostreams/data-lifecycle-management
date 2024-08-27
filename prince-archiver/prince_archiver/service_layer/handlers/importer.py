"""Handlers used to import imaging event into system."""

import asyncio
import logging
from dataclasses import dataclass

from arq import ArqRedis

from prince_archiver.adapters.file import ArchiveFileManager
from prince_archiver.domain.models import ImagingEvent, SrcDirInfo
from prince_archiver.service_layer import messages
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.uow import AbstractUnitOfWork

LOGGER = logging.getLogger(__name__)


async def import_imaging_event(
    message: messages.ImportImagingEvent,
    uow: AbstractUnitOfWork,
):
    LOGGER.info("[%s] Importing imaging event", message.ref_id)

    async with uow:
        if await uow.imaging_events.get_by_ref_id(message.ref_id):
            raise ServiceLayerException("Already imported.")

        imaging_event = ImagingEvent.factory(**message.model_dump())

        uow.imaging_events.add(imaging_event)

        uow.add_message(
            messages.ImportedImagingEvent(
                id=imaging_event.id,
                **message.model_dump(),
            ),
        )

        await uow.commit()


@dataclass
class SrcDirContext:
    file_manager: ArchiveFileManager


async def get_src_dir_info(
    message: messages.ImportedImagingEvent,
    uow: AbstractUnitOfWork,
    *,
    context: SrcDirContext,
):
    async with uow:
        file_manager = context.file_manager
        src_path = file_manager.get_src_path(message.local_path)
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(file_manager.get_file_count(src_path))
            t2 = tg.create_task(file_manager.get_raw_metadata(src_path))

        uow.add_message(
            messages.AddSrcDirInfo(
                ref_id=message.ref_id,
                img_count=t1.result(),
                raw_metadata=t2.result(),
            )
        )


async def add_src_dir_info(
    message: messages.AddSrcDirInfo,
    uow: AbstractUnitOfWork,
):
    async with uow:
        if imaging_event := await uow.imaging_events.get_by_ref_id(message.ref_id):
            imaging_event.add_src_dir_info(
                SrcDirInfo(
                    img_count=message.img_count,
                    raw_metadata=message.raw_metadata,
                )
            )
        await uow.commit()


@dataclass
class PropagateContext:
    redis_client: ArqRedis


async def propagate_new_imaging_event(
    message: messages.ImportedImagingEvent,
    uow: AbstractUnitOfWork,
    *,
    context: PropagateContext,
):
    async with uow:
        dto = messages.InitiateExportEvent(
            ref_id=message.ref_id,
            type=message.type,
        )

        await context.redis_client.enqueue_job(
            "workflow",
            dto.model_dump(mode="json"),
        )
