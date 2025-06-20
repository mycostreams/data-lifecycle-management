import asyncio
import sys

from .api_client import ArchiveParams
from .config import Settings
from .ingest import get_managed_export_ingester


async def main(experiment_id: str):
    settings = Settings()
    remote = f"/scratch-shared/amftrack2024/daily/{experiment_id}.json"
    sbatch_command = (
        "sbatch /gpfs/home4/mkerrwinter/orchestrator/"
        "orchestrator/bash_scripts/downloader_archive.sh"
        " /scratch-shared/amftrack2024/test_tape"
    )
    async with get_managed_export_ingester(settings) as export_ingester:
        await export_ingester.ingest_archive(
            remote, ArchiveParams(experiment_id=experiment_id)
        )
        await export_ingester.run_sbatch_command(sbatch_command, remote)


if __name__ == "__main__":
    experiment_id = sys.argv[1]
    asyncio.run(main(experiment_id))
