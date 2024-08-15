"""Handlers used to import imaging event into system."""

from dataclasses import dataclass

from arq import ArqRedis

from prince_archiver.definitions import EventType
from prince_archiver.domain.models import ConcreteImagingEvent, StitchEvent, VideoEvent
from prince_archiver.service_layer import messages
from prince_archiver.service_layer.exceptions import ServiceLayerException
from prince_archiver.service_layer.uow import AbstractUnitOfWork

from .utils import model_to_dict


async def import_imaging_event(
    message: messages.ImportImagingEvent,
    uow: AbstractUnitOfWork,
):
    async with uow:
        if await uow.imaging_events.get_by_ref_id(message.ref_id):
            raise ServiceLayerException("Already imported.")

        target_cls: type[ConcreteImagingEvent] = (
            StitchEvent if message.params.type == EventType.STITCH else VideoEvent
        )
        param_cls = target_cls.get_param_cls()

        imaging_event = target_cls.factory(
            params=param_cls(**model_to_dict(message.params, exclude={"type"})),
            **model_to_dict(message, exclude={"params"}),
        )
        uow.imaging_events.add(imaging_event)

        uow.add_message(
            messages.ImportedImagingEvent(
                id=message.ref_id,
                **message.model_dump(),
            ),
        )
        await uow.commit()


@dataclass
class Context:
    redis_client: ArqRedis


async def propagate_new_imaging_event(
    message: messages.ImportedImagingEvent,
    uow: AbstractUnitOfWork,
    *,
    context: Context,
):
    async with uow:
        dto = messages.InitiateExportEvent(
            ref_id=message.ref_id,
            type=message.params.type,
        )

        await context.redis_client.enqueue_job(
            "workflow",
            dto.model_dump(mode="json"),
        )
