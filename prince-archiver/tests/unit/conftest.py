from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from prince_archiver.definitions import EventType, System
from prince_archiver.domain.models import EventArchive, ImagingEvent, SrcDirInfo
from prince_archiver.domain.value_objects import Checksum


@pytest.fixture(name="metadata")
def fixture_metadata() -> dict[str, Any]:
    return {
        "application": {
            "application": "test_application",
            "version": "v0.1.0",
            "user": "test_user",
        },
        "camera": {
            "model": "test_model",
            "station_name": "test_station",
            "exposure_time": 0.01,
            "frame_rate": 10.0,
            "frame_size": (1, 1),
            "binning": "1x1",
            "gain": 1,
            "gamma": 1,
            "intensity": [0, 0, 0],
            "bits_per_pixel": 0,
        },
        "stitching": {
            "last_focused_at": "2000-01-01T00:00:00+00:00",
            "grid_size": (1, 1),
        },
    }


@pytest.fixture(name="unexported_imaging_event")
def fixture_unexported_imaging_event() -> ImagingEvent:
    return ImagingEvent.factory(
        ref_id=uuid4(),
        system=System.PRINCE,
        type=EventType.STITCH,
        experiment_id="test_experiment_id",
        timestamp=datetime(2000, 1, 1, tzinfo=UTC),
        src_dir_info=SrcDirInfo(
            local_path=Path("unexported/path"),
            img_count=10,
        ),
        raw_metadata={"key": "value"},
    )


@pytest.fixture(name="exported_imaging_event")
def fixture_exported_imaging_event() -> ImagingEvent:
    imaging_event = ImagingEvent.factory(
        ref_id=uuid4(),
        system=System.PRINCE,
        type=EventType.STITCH,
        experiment_id="test_experiment_id",
        timestamp=datetime(2001, 1, 1, tzinfo=UTC),
        src_dir_info=SrcDirInfo(
            local_path=Path("exported/path"),
            img_count=10,
        ),
        raw_metadata={"key": "value"},
    )

    imaging_event.add_event_archive(
        EventArchive(
            size=10,
            checksum=Checksum(hex="321"),
        )
    )

    return imaging_event
