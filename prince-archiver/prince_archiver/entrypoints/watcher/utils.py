from prince_archiver.definitions import EventType
from prince_archiver.service_layer.external_dto import TimestepDTO
from prince_archiver.service_layer.messages import ImportImagingEvent


def map_external_dto(timestep_dto: TimestepDTO) -> ImportImagingEvent:
    return ImportImagingEvent(
        ref_id=timestep_dto.timestep_id,
        experiment_id=timestep_dto.experiment_id,
        local_path=timestep_dto.img_dir,
        timestamp=timestep_dto.timestamp,
        type=EventType.STITCH,
    )
