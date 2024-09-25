import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Protocol

from prince_archiver.adapters.streams import ConsumerGroup, Stream
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messagebus import MessageBus
from prince_archiver.service_layer.messages import ImportImagingEvent
from prince_archiver.service_layer.streams import Group, IncomingMessage

LOGGER = logging.getLogger(__name__)


class State(Protocol):
    stream: Stream

    def messagebus_factory(self) -> MessageBus: ...


async def stream_ingester(state: State):
    LOGGER.info("Ingesting stream")

    group = ConsumerGroup(
        consumer_name=Group.import_event,
        group_name=Group.import_event,
    )

    async for message in state.stream.stream_group(group, msg_cls=IncomingMessage):
        mapped_message = ImportImagingEvent(
            **message.processed_data().model_dump(),
        )
        messagebus = state.messagebus_factory()

        async with message.process():
            try:
                await messagebus.handle(mapped_message)
            except ServiceLayerException:
                pass


@asynccontextmanager
async def managed_stream_ingester(state: State):
    task = asyncio.create_task(stream_ingester(state))

    yield

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass
