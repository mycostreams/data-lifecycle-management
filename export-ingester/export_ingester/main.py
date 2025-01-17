import asyncio

from .config import Settings
from .ingest import get_managed_export_ingester


async def main():
    settings = Settings()
    async with get_managed_export_ingester(settings) as export_ingester:
        # await export_ingester.ingest(remote, ExportParams(start=start, end=end))
        await export_ingester.run_sbatch_command(settings.SBATCH_COMMAND)
    archive_command = (
        "sbatch --time=22:00:00 --partition=staging --nodes=1"
        " --ntasks=1 --job-name=surf_archive --output=archive_%j.out"
        " --error=archive_%j.err --wrap='surf-archiver-cli archive"
        " --mode=images 2024-12-19'"
    )
    async with get_managed_export_ingester(settings) as ingester:
        await ingester.run_sbatch_command(archive_command)


if __name__ == "__main__":
    asyncio.run(main())
