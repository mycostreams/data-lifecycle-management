"""No pytest in this package: run with `poetry run python -m tests.test_worker`."""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from export_ingester import worker


def test_overview_archiving_is_off_until_enabled():
    ctx = {"settings": SimpleNamespace(OVERVIEW_ARCHIVE_ENABLED=False)}
    with patch.object(worker, "get_managed_export_ingester") as managed:
        asyncio.run(worker.run_overview_archiving(ctx))
    managed.assert_not_called()


def test_overview_crons_registered():
    names = {job.name for job in worker.WorkerSettings.cron_jobs}
    assert {"cron:run_overview_ingestion", "cron:run_overview_archiving"} <= names


if __name__ == "__main__":
    test_overview_archiving_is_off_until_enabled()
    test_overview_crons_registered()
    print("ok")
