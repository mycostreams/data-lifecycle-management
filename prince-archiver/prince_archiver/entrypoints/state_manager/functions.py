import logging
from dataclasses import dataclass

from arq import Retry

from prince_archiver.adapters.streams import Stream
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messagebus import MessagebusFactoryT
from prince_archiver.service_layer.messages import (
    ExportedImagingEvent,
)

from .settings import Settings

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    settings: Settings
    stream: Stream
    messagebus_factory: MessagebusFactoryT


async def run_persist_export(
    ctx: dict,
    input_data: dict,
):
    dto = ExportedImagingEvent.model_validate(input_data)

    state: State = ctx["state"]
    messagebus = state.messagebus_factory()

    try:
        await messagebus.handle(dto)
    except ServiceLayerException as exc:
        job_try: int = ctx["job_try"]
        raise Retry(defer=job_try) from exc
