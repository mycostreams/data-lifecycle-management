from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest

from prince_archiver.service_layer.external_dto import TimestepDTO


@dataclass
class _BaseKwargs:
    timestep_id: UUID = UUID("a8a808e9abbe4544b6f46bed44bf6a70")
    position: int = 3
    plate: int = 1
    cross_date: date = date(2000, 1, 1)
    timestamp: datetime = datetime(2001, 1, 1, tzinfo=UTC)
    image_count: int = 150
    path: Path = Path("/root")


@pytest.fixture(name="base_kwargs")
def fixture_base_kwargs() -> _BaseKwargs:
    return _BaseKwargs()


def test_experiment_id_set(base_kwargs: _BaseKwargs):
    dto = TimestepDTO(**base_kwargs.__dict__)
    assert dto.experiment_id == "20000101_001"
