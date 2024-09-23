from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from prince_archiver.definitions import EventType


class ExportModel(BaseModel):
    id: UUID
    ref_id: UUID
    experiment_id: str
    type: EventType
    url: HttpUrl | None = None
    uploaded_at: datetime
