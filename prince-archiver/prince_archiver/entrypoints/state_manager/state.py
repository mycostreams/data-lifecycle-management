import asyncio
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from functools import partial
from typing import AsyncGenerator

from arq import ArqRedis

from prince_archiver.adapters.streams import Consumer, Stream
from prince_archiver.adapters.subscriber import ManagedSubscriber
from prince_archiver.service_layer.handlers.state import (
    add_data_archive_entry,
    import_imaging_event,
    persist_imaging_event_export,
)
from prince_archiver.service_layer.messagebus import MessageBus, MessagebusFactoryT
from prince_archiver.service_layer.messages import (
    AddDataArchiveEntry,
    ExportedImagingEvent,
    ImportImagingEvent,
)
from prince_archiver.service_layer.streams import Group, IncomingMessage, Streams
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

from .external import SubscriberMessageHandler
from .settings import Settings
from .stream import Ingester, import_handler

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    stop_event: asyncio.Event
    import_ingester: Ingester
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

    stream = Stream(redis=redis, stream=Streams.imaging_events)

    stop_event = asyncio.Event()

    import_ingester = Ingester(
        stream.stream_group(
            consumer=Consumer(Group.state_manager),
            msg_cls=IncomingMessage,
            stop_event=stop_event,
        ),
        handler=partial(import_handler, messagebus_factory=messagebus_factory),
    )

    yield State(
        stop_event=stop_event,
        import_ingester=import_ingester,
        messagebus_factory=messagebus_factory,
        subscriber=ManagedSubscriber(
            connection_url=settings.RABBITMQ_DSN,
            message_handler=SubscriberMessageHandler(messagebus_factory),
        ),
    )

    await exit_stack.aclose()
