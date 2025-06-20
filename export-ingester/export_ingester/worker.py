import logging
import os
from datetime import date

from arq import cron
from arq.connections import RedisSettings
from zoneinfo import ZoneInfo

from .ingest import Settings, get_managed_export_ingester


def configure_logging():
    logging.basicConfig(level=logging.INFO)


async def startup(ctx: dict):
    configure_logging()

    logging.info("Starting up")

    ctx["settings"] = Settings()


async def run_ingestion(ctx: dict, *, _date: date | None = None):
    settings: Settings = ctx["settings"]
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(settings.SBATCH_COMMAND)


async def run_archiving(ctx: dict, *, _date: date | None = None):
    archive_command = (
        "sbatch --time=22:00:00 --partition=staging "
        "--nodes=1 --ntasks=1 --job-name=surf_archive"
        " --output=archive_%j.out --error=archive_%j.err"
        " --wrap='surf-archiver-cli archive --mode=images"
        " 2024-12-19'"
    )
    settings: Settings = ctx["settings"]
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(archive_command)


async def run_video_archiving(ctx: dict, *, _date: date | None = None):
    archive_command = (
        "sbatch --time=22:00:00 --partition=staging "
        "--nodes=1 --ntasks=1 --job-name=surf_archive"
        " --output=archive_%j.out --error=archive_%j.err"
        " --wrap='surf-archiver-cli archive --mode=video"
        " 2024-12-19'"
    )
    settings: Settings = ctx["settings"]
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(archive_command)


class WorkerSettings:
    cron_jobs = [
        cron(run_archiving, hour={1}, minute={21}),
        cron(run_video_archiving, hour={6}, minute={21}),
        cron(run_ingestion, hour={11}, minute={21}),
    ]
    timezone = ZoneInfo("Europe/Amsterdam")

    on_startup = startup

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_DSN", "redis://localhost:6379"),
    )
