import asyncio
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Awaitable, Callable

import aiofiles
import aiofiles.os
import s3fs
from aiofiles.tempfile import TemporaryDirectory
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import WorkerSettings as _WorkerSettings
from .config import get_worker_settings
from .db import AbstractUnitOfWork, UnitOfWork, get_session_maker
from .dto import TimestepDTO
from .file import acompress, atar, managed_file_system
from .logging import configure_logging
from .models import ObjectStoreEntry
from .utils import now

LOGGER = logging.getLogger(__name__)


@dataclass
class Upload:
    bucket: str
    key: str
    expires_at: datetime = field(default_factory=lambda: now() + timedelta(days=30))


async def upload_workflow(ctx: dict, data: TimestepDTO) -> Upload:
    settings: _WorkerSettings = ctx["settings"]
    s3: s3fs.S3FileSystem = ctx["s3"]
    pool: ProcessPoolExecutor = ctx["pool"]

    img_dir = settings.DATA_DIR / data.timestep_dir_name / data.img_dir_name
    files = map(lambda path: img_dir / path, await aiofiles.os.listdir(img_dir))

    async with AsyncExitStack() as stack:
        temp_dirs = await asyncio.gather(
            *(stack.enter_async_context(TemporaryDirectory()) for _ in range(2)),
        )
        temp_img_dir, temp_archive_dir = map(Path, temp_dirs)
        temp_archive_path = temp_archive_dir / data.archive_name

        LOGGER.info("Compressing")
        await asyncio.gather(
            *(acompress(file, temp_img_dir / file.name, pool) for file in files),
        )

        LOGGER.info("Tarring")
        await atar(temp_img_dir, temp_archive_path, pool)

        LOGGER.info("Uploading")
        await s3._put_file(temp_archive_path, f"{settings.AWS_BUCKET_NAME}/{data.key}")

    return Upload(bucket=settings.AWS_BUCKET_NAME, key=data.key)


async def workflow(
    ctx: dict,
    input_data: dict,
    *,
    upload_workflow: Callable[[dict, TimestepDTO], Awaitable[Upload]] = upload_workflow,
):
    data = TimestepDTO.model_validate(input_data)
    uow: AbstractUnitOfWork = ctx["uow"]
    async with uow:
        upload = await upload_workflow(ctx, data)
        if timestep := await uow.timestamps.get(id=data.timestep_id):
            timestep.object_store_entry = ObjectStoreEntry(**upload.__dict__)
        await uow.commit()


async def startup(ctx):
    configure_logging()

    settings = get_worker_settings()
    ctx["settings"] = settings

    exit_stack = await AsyncExitStack().__aenter__()
    ctx["exit_stack"] = exit_stack

    ctx["pool"] = exit_stack.enter_context(ProcessPoolExecutor())
    ctx["s3"] = await exit_stack.enter_async_context(managed_file_system(settings))

    ctx["sessionmaker"] = get_session_maker(str(settings.POSTGRES_DSN))


async def on_job_start(ctx: dict):
    session_maker: async_sessionmaker[AsyncSession] = ctx["sessionmaker"]
    ctx["uow"] = UnitOfWork(session_maker)


async def shutdown(ctx: dict):
    exit_stack: AsyncExitStack = ctx["exit_stack"]
    await exit_stack.aclose()


class WorkerSettings:

    functions = [workflow]
    max_jobs = 2
    on_startup = startup
    on_shutdown = shutdown
    on_job_start = on_job_start

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
