import logging
import os
from datetime import date

import structlog
from arq import cron
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from .ingest import Settings, get_managed_export_ingester

LOGGER = logging.getLogger(__name__)


def configure_logging():
    _pre_chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    structlog.configure(
        processors=_pre_chain
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_pre_chain,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


async def startup(ctx: dict):
    configure_logging()

    LOGGER.info("Starting up")

    ctx["settings"] = Settings()

    await run_ingestion(ctx)


async def run_ingestion(ctx: dict, *, _date: date | None = None):
    settings: Settings = ctx["settings"]
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(settings.SBATCH_COMMAND)


async def run_video_ingestion(ctx: dict, *, _date: date | None = None):
    settings: Settings = ctx["settings"]
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(settings.SBATCH_VIDEO_COMMAND)


# `--mem=64G`, because the staging default is 7G per core and both archive crons were
# OOM-killed at it on most days since 2026-09-03.
#
# 7G was never enough by design: `ExperimentFileSystem.batch_size` is -1, so `get_files`
# asks s3fs for unbounded concurrency and pulls every tar of an experiment-date group at
# once. Peak RSS therefore scales with the group, which nothing bounds. Raising the
# ceiling stops the daily failures; bounding `batch_size` is the smaller-footprint fix
# and wants a measurement of what the groups actually cost first.
_ARCHIVE_SBATCH = (
    "sbatch --time=22:00:00 --partition=staging --nodes=1 --ntasks=1 --mem=64G"
    " --job-name=surf_archive"
    " --mail-type=FAIL,TIME_LIMIT --mail-user=s.vstaalduine@amolf.nl"
    " --output=archive_%j.out --error=archive_%j.err"
    " --wrap='surf-archiver-cli archive --mode={mode}'"
)


async def run_archiving(ctx: dict, *, _date: date | None = None):
    archive_command = _ARCHIVE_SBATCH.format(mode="images")
    settings: Settings = ctx["settings"]
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(archive_command)


async def run_video_archiving(ctx: dict, *, _date: date | None = None):
    archive_command = _ARCHIVE_SBATCH.format(mode="videos")
    settings: Settings = ctx["settings"]
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(archive_command)


class WorkerSettings:
    health_check_key = "arq:health:export-ingester"
    health_check_interval = 300

    cron_jobs = [
        cron(run_archiving, hour={1}, minute={21}),
        cron(run_video_ingestion, hour={7}, minute={16}),
        cron(run_video_archiving, hour={18}, minute={21}),
        cron(run_ingestion, hour={4}, minute={21}),
    ]
    timezone = ZoneInfo("Europe/Amsterdam")

    on_startup = startup

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
