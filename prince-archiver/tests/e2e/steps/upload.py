from datetime import date, datetime, timezone
from textwrap import dedent
from uuid import UUID, uuid4

import httpx
from behave import *
from behave.api.async_step import async_run_until_complete
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from prince_archiver.dto import TimestepMeta
from prince_archiver.test_utils.utils import Timer


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
@async_run_until_complete
async def step_impl(context, timeout=30):

    db_engine: AsyncEngine = context.db_engine
    timestep_id: UUID = context.timestep_id

    raw_stmt = dedent(
        """
        SELECT COUNT(1)
        FROM object_store_entry 
        WHERE timestep_id=:timestep_id
        """
    )

    async with db_engine.begin() as conn:
        timer = Timer()
        exists = False
        while not exists and timer.delta < timeout:
            _exists: int = await conn.scalar(
                text(raw_stmt),
                {"timestep_id": timestep_id.hex},
            )
            exists = bool(_exists)

        assert exists


@then("the processed timestep is available in the object store")
def step_impl(context, timeout=30):
    client: httpx.Client = context.client

    expected_path = "mycostreams/2000_01/20000101_0000.tar"

    resp = client.head(f"http://localhost:9091/{expected_path}")

    assert resp.status_code == 200
