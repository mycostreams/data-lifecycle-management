from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from prince_archiver.definitions import EventType


class ExportModel(BaseModel):
    id: UUID
    ref_id: UUID
    uploaded_at: datetime
    url: HttpUrl | None = None
    type: EventType
