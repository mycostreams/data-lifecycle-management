import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.streams import ConsumerGroup, Group, Stream
from prince_archiver.definitions import SrcDirKey

from .settings import IngesterSettings

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    settings: IngesterSettings
    stream: Stream
    path_manager: PathManager


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

        if message.src_dir_info.staging_path:
            src_dir = state.path_manager.get_src_dir(
                SrcDirKey.STAGING,
                message.src_dir_info.staging_path,
            )
            await src_dir.rm()

        await state.stream.ack(id, group=group)


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

        src_dir = state.path_manager.get_src_dir(
            message.system,
            message.src_dir_info.local_path,
        )
        await src_dir.rm()
        await state.stream.ack(id, group=group)
