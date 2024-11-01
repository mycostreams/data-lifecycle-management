import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from functools import partial
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from arq import ArqRedis

from prince_archiver.adapters.file import PathManager
from prince_archiver.adapters.streams import Stream
from prince_archiver.file import managed_file_system
from prince_archiver.service_layer.export import (
    Exporter,
    ExportHandler,
    Publisher,
    StreamMessageHandler,
)
from prince_archiver.service_layer.handlers.utils import get_target_key
from prince_archiver.service_layer.streams import Streams

from .settings import Settings

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    stream: Stream
    stream_message_handler: StreamMessageHandler
    export_handler: ExportHandler


@asynccontextmanager
async def get_managed_state(
    redis: ArqRedis,
    *,
    settings: Settings | None = None,
) -> AsyncGenerator[State, None]:
    exit_stack = await AsyncExitStack().__aenter__()

    settings = settings or Settings()

    s3 = await exit_stack.enter_async_context(managed_file_system(settings))

    stream = Stream(
        redis=redis,
        stream=Streams.new_imaging_event,
    )

    yield State(
        stream=stream,
        stream_message_handler=StreamMessageHandler(redis=redis),
        export_handler=ExportHandler(
            stream=stream,
            exporter=Exporter(
                s3=s3,
                key_generator=partial(
                    get_target_key,
                    bucket=settings.AWS_BUCKET_NAME,
                ),
                path_manager=PathManager(settings.SRC_DIR),
            ),
            publisher=Publisher(redis=redis),
        ),
    )

    await exit_stack.aclose()
