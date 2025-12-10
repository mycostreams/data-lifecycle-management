from datetime import UTC

from prince_archiver.definitions import EventType
from prince_archiver.service_layer.dto import CommonImagingEvent


def get_target_key(imaging_event: CommonImagingEvent, bucket: str) -> str:
    """
    Creates a target key for an imaging event based on the contents of the message.

    Final path is:
    /<bucket>/<[videos, images]>/<experiment_id>/<YYYYMMDD>/<HHmmss>.tar

    Args:
        imaging_event (CommonImagingEvent): Metadata of imaging event
        bucket (str): Bucket where the video comes goes to

    Returns:
        str: address where the data will get uploaded
    """
    match imaging_event.type:
        case EventType.STITCH:
            event_type = "images"
        case EventType.VIDEO:
            event_type = "videos"
        case EventType.OVERVIEW:
            event_type = "overview"
        case other:
            raise KeyError(f"Unknown event type {other}")

    # event_type = "images" if imaging_event.type == EventType.STITCH else "videos"

    ref_timestamp = imaging_event.timestamp.astimezone(UTC)

    date_folder = ref_timestamp.strftime("%Y%m%d")
    file_name = ref_timestamp.strftime("%H%M%S.tar")

    return "/".join(
        (bucket, event_type, imaging_event.experiment_id, date_folder, file_name)
    )
