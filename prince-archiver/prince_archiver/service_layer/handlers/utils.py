from datetime import UTC

from prince_archiver.definitions import EventType
from prince_archiver.service_layer.dto import CommonImagingEvent


def get_target_key(imaging_event: CommonImagingEvent, bucket: str) -> str:
    event_type = "images" if imaging_event.type == EventType.STITCH else "videos"

    ref_timestamp = imaging_event.timestamp.astimezone(UTC)

    date_folder = ref_timestamp.strftime("%Y%m%d")
    file_name = ref_timestamp.strftime("%H%M%S.tar")

    return "/".join(
        (bucket, event_type, imaging_event.experiment_id, date_folder, file_name)
    )
