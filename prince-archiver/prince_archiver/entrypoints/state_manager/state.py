import logging
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from functools import partial
from typing import AsyncGenerator

from arq import ArqRedis

from prince_archiver.adapters.streams import Stream
from prince_archiver.adapters.subscriber import ManagedSubscriber
from prince_archiver.service_layer.handlers.archive import add_data_archive_entry
from prince_archiver.service_layer.handlers.export import persist_imaging_event_export
from prince_archiver.service_layer.handlers.ingest import import_imaging_event
from prince_archiver.service_layer.messagebus import MessageBus, MessagebusFactoryT
from prince_archiver.service_layer.messages import (
    AddDataArchiveEntry,
    ExportedImagingEvent,
    ImportImagingEvent,
)
from prince_archiver.service_layer.streams import Streams
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

from .external import SubscriberMessageHandler
from .settings import Settings
from .stream import StreamMessageHandler

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    stream: Stream
    stream_message_handler: StreamMessageHandler
    messagebus_factory: MessagebusFactoryT
    subscriber: ManagedSubscriber


@asynccontextmanager
async def get_managed_state(
    redis: ArqRedis,
    *,
    settings: Settings | None,
) -> AsyncGenerator[State, None]:
    exit_stack = await AsyncExitStack().__aenter__()

    settings = settings or Settings()

    uow_factory = partial(
        UnitOfWork,
        get_session_maker(str(settings.POSTGRES_DSN)),
    )

    messagebus_factory = MessageBus.factory(
        handlers={
            ImportImagingEvent: [import_imaging_event],
            ExportedImagingEvent: [persist_imaging_event_export],
            AddDataArchiveEntry: [add_data_archive_entry],
        },
        uow=uow_factory,
    )

    stream = Stream(redis=redis, stream=Streams.new_imaging_event)

    yield State(
        stream=stream,
        stream_message_handler=StreamMessageHandler(messagebus_factory),
        messagebus_factory=messagebus_factory,
        subscriber=ManagedSubscriber(
            connection_url=settings.RABBITMQ_DSN,
            message_handler=SubscriberMessageHandler(messagebus_factory),
        ),
    )

    await exit_stack.aclose()
