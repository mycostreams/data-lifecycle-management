from datetime import date, datetime, timezone
from uuid import UUID, uuid4
from timeit import default_timer
from textwrap import dedent

import httpx
from behave import *
from sqlalchemy import Connection, text

from prince_archiver.dto import TimestepMeta


@given("the watcher and worker are running")
def step_impl(context):
    pass


@when("a timestep is added")
def step_impl(context):
    client: httpx.Client = context.client

    context.timestep_id = uuid4()

    meta = TimestepMeta(
        timestep_id=context.timestep_id,
        plate=1,
        cross_date=date(2000, 1, 1),
        position=1,
        timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc),
    )

    resp = client.post(
        "http://localhost:8001/timestep",
        json=meta.model_dump(mode="json"),
    )

    assert resp.status_code == 200


@then("the results are stored locally")
def step_impl(context, timeout=30):
    conn: Connection = context.db_conn
    timestep_id: UUID = context.timestep_id

    raw_stmt = """\
        SELECT COUNT(1)
        FROM object_store_entry 
        WHERE timestep_id=:timestep_id
    """

    exists = False

    ref = default_timer()
    now = ref

    while exists is False and (now - ref) < timeout:
        cursor = conn.execute(
            text(dedent(raw_stmt)), 
            {"timestep_id": timestep_id.hex}
        )
        exists = bool(cursor.scalar())
        now = default_timer()

    assert exists


@then("the processed timestep is available in the object store")
def step_impl(context, timeout=30):
    client: httpx.Client = context.client

    expected_path = "mycostreams/2000_01/20000101_0000.tar"

    resp = client.head(f"http://localhost:9091/{expected_path}")

    assert resp.status_code == 200
