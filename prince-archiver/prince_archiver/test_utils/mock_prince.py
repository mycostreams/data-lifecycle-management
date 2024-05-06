import logging
import os
import time
from datetime import date
from pathlib import Path
from uuid import uuid4

from prince_archiver.dto import TimestepMeta
from prince_archiver.logging import configure_logging
from prince_archiver.utils import now

from .utils import make_timestep_directory


def _create_meta() -> TimestepMeta:
    return TimestepMeta(
        plate=1,
        cross_date=date(2000, 1, 1),
        position=1,
        timestamp=now(),
    )


def main():
    """Add new timestep directory every minute."""
    configure_logging()

    data_dir = Path(os.environ.get("DATA_DIR", "/app/data"))

    while True:
        target_dir = data_dir / uuid4().hex[:6]
        make_timestep_directory(target_dir, _create_meta())

        logging.info("Directory added: %s", target_dir)

        time.sleep(60)


if __name__ == "__main__":
    main()
