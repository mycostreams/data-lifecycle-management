import asyncio
import logging
from dataclasses import dataclass
from functools import partial

import redis.asyncio as redis

from prince_archiver.adapters.s3 import file_system_factory
from prince_archiver.adapters.streams import Consumer, Stream
from prince_archiver.adapters.subscriber import ManagedSubscriber
from prince_archiver.api import APIState
from prince_archiver.service_layer.dto import (
    AddDataArchiveEntry,
    ExportedImagingEvent,
    ImportImagingEvent,
)
from prince_archiver.service_layer.handlers.state import (
    add_data_archive_entry,
    import_imaging_event,
    persist_imaging_event_export,
)
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.streams import (
    Group,
    IncomingExportMessage,
    IncomingMessage,
    Streams,
)
from prince_archiver.service_layer.uow import UnitOfWork, get_session_maker

from .consumers import (
    Ingester,
    SubscriberMessageHandler,
    import_handler,
    upload_event_handler,
)
from .settings import Settings

LOGGER = logging.getLogger(__name__)


@dataclass
class State(APIState):
    redis: redis.Redis
    stop_event: asyncio.Event
    import_ingester: Ingester
    export_ingester: Ingester
    subscriber: ManagedSubscriber


def get_state(
    *,
    settings: Settings | None = None,
) -> State:
    settings = settings or Settings()

    redis_client = redis.from_url(str(settings.REDIS_DSN))

    sessionmaker = get_session_maker(str(settings.POSTGRES_DSN))
    messagebus_factory = MessageBus.factory(
        handlers={
            ImportImagingEvent: [import_imaging_event],
            ExportedImagingEvent: [persist_imaging_event_export],
            AddDataArchiveEntry: [add_data_archive_entry],
        },
        uow=partial(UnitOfWork, sessionmaker),
    )

    import_stream = Stream(redis=redis_client, name=Streams.imaging_events)
    upload_stream = Stream(redis=redis_client, name=Streams.upload_events)

    stop_event = asyncio.Event()

    return State(
        file_system=file_system_factory(settings),
        redis=redis_client,
        sessionmaker=sessionmaker,
        stop_event=stop_event,
        import_ingester=Ingester(
            import_stream.stream_group(
                consumer=Consumer(Group.state_manager),
                msg_cls=IncomingMessage,
                stop_event=stop_event,
            ),
            handler=partial(
                import_handler,
                messagebus_factory=messagebus_factory,
            ),
        ),
        export_ingester=Ingester(
            upload_stream.stream_group(
                consumer=Consumer(Group.state_manager),
                msg_cls=IncomingExportMessage,
                stop_event=stop_event,
            ),
            handler=partial(
                upload_event_handler,
                messagebus_factory=messagebus_factory,
            ),
        ),
        subscriber=ManagedSubscriber(
            connection_url=settings.RABBITMQ_DSN,
            message_handler=SubscriberMessageHandler(messagebus_factory),
        ),
    )
