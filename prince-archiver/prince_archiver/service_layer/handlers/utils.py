from typing import Any

from pydantic import BaseModel

from prince_archiver.definitions import EventType
from prince_archiver.domain.models import ImagingEvent


def get_target_key(imaging_event: ImagingEvent, bucket: str) -> str:
    event_type = "images" if imaging_event.type == EventType.STITCH else "videos"
    base = imaging_event.timestamp.strftime("%Y%m%d/%H%M.tar")

    return f"{bucket}/{event_type}/{imaging_event.experiment_id}/{base}"


def model_to_dict(
    model: BaseModel,
    *,
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    model_as_dict = dict(model)
    if exclude:
        return {k: v for k, v in model_as_dict.items() if k not in exclude}
    return model_as_dict
