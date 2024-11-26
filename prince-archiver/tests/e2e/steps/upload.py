from uuid import uuid4
from typing import Callable

import httpx
from behave import *  # noqa:

from prince_archiver.service_layer.dto import NewImagingEvent
from prince_archiver.test_utils.utils import Timer


@given("the containers are running")
def step_impl(context):
    response: dict = context.get_exports()
    context.initial_count = response["count"]


@when("an event is added")
def step_impl(context):
    client: httpx.Client = context.client

    ref_id = uuid4()

    context.ref_id = ref_id

    event = NewImagingEvent(
        ref_id=ref_id,
        experiment_id=f"test-id-{ref_id.hex[:6]}",
        timestamp="2000-01-01T00:00:00+00:00",
        type="stitch",
        system="prince",
        local_path=ref_id.hex[:6],
        img_count=1,
        metadata={
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
        },
    )

    resp = client.post(
        "http://localhost:8001/timestep",
        json=event.model_dump(mode="json"),
    )

    assert resp.status_code == 200


@then("the export count should be incremented")
def step_impl(context, timeout=10):
    get_exports: Callable[[], dict] = context.get_exports

    initial_count: int = context.initial_count

    timer = Timer()
    while (
        (data := get_exports())
        and data["count"] <= initial_count
        and timer.delta <= timeout
    ):
        continue

    assert initial_count < data["count"]
