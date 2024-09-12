import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from prince_archiver.adapters.file import ArchiveFileManager
from prince_archiver.adapters.streams import ConsumerGroup, Group, Stream
from prince_archiver.definitions import System

from .settings import IngesterSettings

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    settings: IngesterSettings
    stream: Stream
    file_system: ArchiveFileManager = field(default_factory=ArchiveFileManager)
    event: asyncio.Event = field(default_factory=asyncio.Event)


async def run_trim(ctx: dict):
    state: State = ctx["state"]
    trim_to = datetime.now(tz=UTC) - timedelta(days=5)
    await state.stream.trim(trim_to)


async def delete_staging(ctx: dict):
    LOGGER.info("Deleting staging files")
    state: State = ctx["state"]
    ref = datetime.now(tz=UTC) - state.settings.STAGING_LIFESPAN

    group = ConsumerGroup(
        consumer_name=Group.delete_staging,
        group_name=Group.delete_staging,
    )

    async for id, message in state.stream.stream_group(group):
        if message.timestamp > ref:
            break

        LOGGER.info("[%s] Deleting staging directory", message.ref_id)
        if state.settings.STAGING_DIR and message.src_dir_info.staging_path:
            await state.file_system.rm_tree(
                state.settings.STAGING_DIR / message.src_dir_info.staging_path
            )

        await state.stream.ack(id, group=group)


def get_src_dir(system: System, settings: IngesterSettings) -> Path:
    match system:
        case System.PRINCE:
            return settings.PRINCE_DIR
        case _:
            raise ValueError


async def delete_src(ctx: dict):
    LOGGER.info("Deleting src files")

    state: State = ctx["state"]
    ref = datetime.now(tz=UTC) - state.settings.SRC_LIFESPAN

    group = ConsumerGroup(
        consumer_name=Group.delete_src,
        group_name=Group.delete_src,
    )

    async for id, message in state.stream.stream_group(group):
        if message.timestamp > ref:
            break

        LOGGER.info("[%s] Deleting src directory", message.ref_id)

        path = get_src_dir(message.system, state.settings)
        await state.file_system.rm_tree(
            path / message.src_dir_info.local_path,
        )
        await state.stream.ack(id, group=group)
