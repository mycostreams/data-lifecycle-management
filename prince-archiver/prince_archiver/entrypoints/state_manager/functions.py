import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

from arq import Retry

from prince_archiver.adapters.messenger import Message, Messenger
from prince_archiver.adapters.streams import Stream
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.messagebus import MessagebusFactoryT
from prince_archiver.service_layer.messages import (
    ExportedImagingEvent,
)
from prince_archiver.service_layer.uow import UnitOfWork

from .settings import Settings

LOGGER = logging.getLogger(__name__)


@dataclass
class State:
    settings: Settings
    stream: Stream
    uow_factory: Callable[[], UnitOfWork]
    messagebus_factory: MessagebusFactoryT
    messenger: Messenger | None = None


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


async def run_reporting(ctx: dict, *, _date: date | None = None):
    state: State = ctx["state"]
    report_date = _date or date.today() - timedelta(days=1)

    if messenger := state.messenger:
        async with state.uow_factory() as uow:
            stats = filter(
                lambda stats: stats.date == report_date,
                await uow.read.get_daily_stats(start=report_date),
            )
            if daily_stats := next(stats, None):
                await messenger.publish(Message.DAILY_STATS, **daily_stats.__dict__)
