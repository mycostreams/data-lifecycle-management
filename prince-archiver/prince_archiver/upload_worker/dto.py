from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field

from prince_archiver.utils import now


class Upload(BaseModel):

    timestep_id: UUID
    bucket: str
    key: str
    expires_at: datetime = Field(default_factory=lambda: now() + timedelta(days=30))
