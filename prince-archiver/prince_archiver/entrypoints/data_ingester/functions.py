import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.streams import ConsumerGroup, Stream
from prince_archiver.definitions import SrcDirKey
from prince_archiver.service_layer.streams import Group, IncomingMessage

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

    async for message in state.stream.stream_group(group, msg_cls=IncomingMessage):
        data = message.processed_data()
        if data.timestamp > ref:
            break

        LOGGER.info("[%s] Deleting staging directory", data.ref_id)

        if data.src_dir_info.staging_path:
            src_dir = state.path_manager.get_src_dir(
                SrcDirKey.STAGING,
                data.src_dir_info.staging_path,
            )
        async with message.process():
            await src_dir.rm()


async def delete_src(ctx: dict):
    LOGGER.info("Deleting src files")

    state: State = ctx["state"]
    ref = datetime.now(tz=UTC) - state.settings.SRC_LIFESPAN

    group = ConsumerGroup(
        consumer_name=Group.delete_src,
        group_name=Group.delete_src,
    )

    async for message in state.stream.stream_group(group, msg_cls=IncomingMessage):
        data = message.processed_data()
        if data.timestamp > ref:
            break

        LOGGER.info("[%s] Deleting src directory", data.ref_id)

        src_dir = state.path_manager.get_src_dir(
            data.system,
            data.src_dir_info.local_path,
        )
        async with message.process():
            await src_dir.rm()
