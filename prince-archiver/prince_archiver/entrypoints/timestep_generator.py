import logging
import os
import time
from datetime import date, datetime
from pathlib import Path

from prince_archiver.dto import ExperimentDTO
from prince_archiver.logging import configure_logging
from prince_archiver.utils import make_timestep_directory


def main():
    """Add new timestep directory every minute."""

    configure_logging()

    target_dir = Path(os.environ.get("DATA_DIR", "/app/data"))

    experiment = ExperimentDTO(plate=1, CrossDate=date(2000, 1, 1))

    while True:
        new_folder = make_timestep_directory(
            experiment=experiment,
            timestamp=datetime.now(),
            target_dir=target_dir,
        )

        logging.info("Directory added: %s", new_folder)

        time.sleep(60)


if __name__ == "__main__":
    main()
