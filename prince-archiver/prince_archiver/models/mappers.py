"""Definition of mappers."""

from typing import Type

from sqlalchemy import ColumnElement
from sqlalchemy.orm import composite, registry, relationship

from prince_archiver.domain import models as domain_models
from prince_archiver.domain import value_objects as vo

from . import v2 as data_models


def get_exclude_fields(model_cls: Type[data_models.Base]) -> list[ColumnElement]:
    return [
        model_cls.created_at.expression,
        model_cls.updated_at.expression,
    ]


def init_mappers():
    mapper_registry = registry()

    data_archive_member_mapper = mapper_registry.map_imperatively(
        domain_models.DataArchiveMember,
        data_models.DataArchiveMember.__table__,
        properties={
            "_imaging_event_id": (
                data_models.DataArchiveMember.imaging_event_id.expression
            )
        },
        exclude_properties=get_exclude_fields(data_models.DataArchiveMember),
    )

    object_store_entry_mapper = mapper_registry.map_imperatively(
        domain_models.ObjectStoreEntry,
        data_models.ObjectStoreEntry.__table__,
        properties={
            "_imaging_event_id": (
                data_models.ObjectStoreEntry.imaging_event_id.expression
            )
        },
        exclude_properties=get_exclude_fields(data_models.ObjectStoreEntry),
    )

    archive_checksum_mapper = mapper_registry.map_imperatively(
        vo.Checksum,
        data_models.ArchiveChecksum.__table__,
        properties={
            "_event_archive_id": (
                data_models.ArchiveChecksum.event_archive_id.expression
            ),
        },
        exclude_properties=[
            data_models.ArchiveChecksum.id,
            *get_exclude_fields(data_models.ArchiveChecksum),
        ],
    )

    event_archive_mapper = mapper_registry.map_imperatively(
        domain_models.EventArchive,
        data_models.EventArchive.__table__,
        properties={
            "checksum": relationship(
                archive_checksum_mapper,
                uselist=False,
            ),
        },
        exclude_properties=get_exclude_fields(data_models.EventArchive),
    )

    stitch_params_mapper = mapper_registry.map_imperatively(
        domain_models.StitchParams,
        data_models.StitchParams.__table__,
        properties={
            "grid_size": composite(vo.GridSize, "_grid_row", "_grid_col"),
            "_grid_row": data_models.StitchParams.grid_row.expression,
            "_grid_col": data_models.StitchParams.grid_col.expression,
            "_imaging_event_id": (data_models.StitchParams.imaging_event_id.expression),
        },
        exclude_properties=get_exclude_fields(data_models.StitchParams),
    )

    video_params_mapper = mapper_registry.map_imperatively(
        domain_models.VideoParams,
        data_models.VideoParams.__table__,
        exclude_properties=get_exclude_fields(data_models.VideoParams),
    )

    imaging_event_mapper = mapper_registry.map_imperatively(
        domain_models.ImagingEvent,
        data_models.ImagingEvent.__table__,
        properties={
            "location": composite(vo.Location, "_system", "_system_position"),
            "event_archive": relationship(event_archive_mapper, uselist=False),
            "object_store_entry": relationship(
                object_store_entry_mapper,
                uselist=False,
            ),
            "data_archive_member": relationship(
                data_archive_member_mapper,
                uselist=False,
            ),
            "_system": data_models.ImagingEvent.system.expression,
            "_system_position": data_models.ImagingEvent.system_position.expression,
        },
        exclude_properties=get_exclude_fields(data_models.ImagingEvent),
    )

    mapper_registry.map_imperatively(
        domain_models.StitchEvent,
        inherits=imaging_event_mapper,
        properties={
            "_params": relationship(stitch_params_mapper, uselist=False),
        },
    )

    mapper_registry.map_imperatively(
        domain_models.VideoEvent,
        inherits=imaging_event_mapper,
        properties={
            "_params": relationship(video_params_mapper, uselist=False),
        },
    )
