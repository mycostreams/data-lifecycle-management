from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

from arq import create_pool
from arq.connections import RedisSettings

from prince_archiver.config import WatcherSettings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.dto import TimestepDTO
from prince_archiver.messagebus import MessageBus

from .handlers import ArqHandler, add_to_db


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

    redis = await create_pool(
        RedisSettings.from_dsn(str(settings.REDIS_DSN)),
    )

    messagebus = MessageBus(
        handlers={TimestepDTO: [add_to_db, ArqHandler(redis)]},
        uow=UnitOfWork(
            get_session_maker(str(settings.POSTGRES_DSN)),
        ),
    )

    yield Context(settings=settings, messagebus=messagebus)

    await redis.aclose()
