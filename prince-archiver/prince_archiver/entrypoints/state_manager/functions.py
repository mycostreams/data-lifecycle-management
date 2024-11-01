import logging

from arq import Retry

from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messages import (
    ExportedImagingEvent,
)

from .state import State

LOGGER = logging.getLogger(__name__)


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
