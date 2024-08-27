from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import partial
from typing import AsyncGenerator

from arq import create_pool
from arq.connections import RedisSettings

from prince_archiver.adapters.file import ArchiveFileManager
from prince_archiver.config import WatcherSettings
from prince_archiver.models import init_mappers
from prince_archiver.service_layer.handlers.importer import (
    PropagateContext,
    SrcDirContext,
    add_src_dir_info,
    get_src_dir_info,
    import_imaging_event,
    propagate_new_imaging_event,
)
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import (
    AddSrcDirInfo,
    ImportedImagingEvent,
    ImportImagingEvent,
)
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker


@dataclass
class Context:
    settings: WatcherSettings
    messagebus: MessageBus


@asynccontextmanager
async def managed_context(
    *,
    _settings: WatcherSettings | None = None,
) -> AsyncGenerator[Context, None]:
    settings = _settings or WatcherSettings()

    init_mappers()

    redis = await create_pool(
        RedisSettings.from_dsn(str(settings.REDIS_DSN)),
    )

    messagebus = MessageBus(
        handlers={
            ImportImagingEvent: [import_imaging_event],
            ImportedImagingEvent: [
                partial(
                    get_src_dir_info,
                    context=SrcDirContext(
                        file_manager=ArchiveFileManager(base_path=settings.DATA_DIR),
                    ),
                ),
                partial(
                    propagate_new_imaging_event,
                    context=PropagateContext(redis_client=redis),
                ),
            ],
            AddSrcDirInfo: [add_src_dir_info],
        },
        uow=UnitOfWork(
            get_session_maker(str(settings.POSTGRES_DSN)),
        ),
    )

    yield Context(settings=settings, messagebus=messagebus)

    await redis.aclose()
