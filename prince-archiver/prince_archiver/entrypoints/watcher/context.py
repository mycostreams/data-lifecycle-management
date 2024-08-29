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
    import_imaging_event,
    propagate_new_imaging_event,
)
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import (
    ImportedImagingEvent,
    ImportImagingEvent,
)
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker


@dataclass
class Context:
    settings: WatcherSettings
    messagebus: MessageBus
    file_manager: ArchiveFileManager | None = None


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
                    propagate_new_imaging_event,
                    context=PropagateContext(redis_client=redis),
                ),
            ],
        },
        uow=UnitOfWork(
            get_session_maker(str(settings.POSTGRES_DSN)),
        ),
    )

    yield Context(
        settings=settings,
        file_manager=ArchiveFileManager(base_path=settings.DATA_DIR),
        messagebus=messagebus,
    )

    await redis.aclose()
