import logging
from pathlib import Path

from watchfiles import watch

from prince_archiver.config import Settings, get_settings
from prince_archiver.db import UnitOfWork, get_session_maker
from prince_archiver.logging import configure_logging
from prince_archiver.watcher import (
    DEFAULT_HANDLERS,
    TimestepHandler,
    filter_on_final_image,
)


def main(*, _settings: Settings | None = None):

    configure_logging()

    settings = _settings or get_settings()

    handler = TimestepHandler(
        handlers=DEFAULT_HANDLERS,
        unit_of_work=UnitOfWork(
            get_session_maker(str(settings.POSTGRES_DSN)),
        ),
    )

    logging.info("Watching %s", settings.DATA_DIR)

    for changes in watch(settings.DATA_DIR, watch_filter=filter_on_final_image):
        for _, filepath in changes:
            handler(Path(filepath).relative_to(settings.DATA_DIR))


if __name__ == "__main__":
    main()
