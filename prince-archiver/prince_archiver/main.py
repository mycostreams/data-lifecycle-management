import time

from .config import Settings, get_settings
from .db import UnitOfWork, get_session_maker
from .logging import configure_logging
from .watcher import NewTimestepHandler, Watcher

configure_logging()


def main(*, _settings: Settings | None = None):

    settings = _settings or get_settings()

    handler = NewTimestepHandler(
        archive_dir=settings.ARCHIVE_DIR,
        unit_of_work=UnitOfWork(
            get_session_maker(str(settings.POSTGRES_DSN)),
        ),
    )

    with Watcher(handler, settings.DATA_DIR):
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()
