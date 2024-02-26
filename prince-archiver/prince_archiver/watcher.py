import logging
from pathlib import Path

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from .db import AbstractUnitOfWork
from .dto import TimestepDTO
from .handlers import DEFAULT_HANDLERS, HandlerT
from .utils import parse_timestep_dir

LOGGER = logging.getLogger(__name__)


class Watcher:

    def __init__(
        self,
        handler: "NewTimestepHandler",
        data_dir: Path,
    ):
        self.handler = handler
        self.data_dir = data_dir

    def __enter__(self):

        self.observer = Observer()
        self.observer.schedule(self.handler, self.data_dir, recursive=True)
        self.observer.start()

        LOGGER.info("Watching %s", self.data_dir)

        return self

    def __exit__(self, *_):
        self.observer.stop()
        self.observer.join()


class NewTimestepHandler(PatternMatchingEventHandler):

    FILE_NAME = "*/Img/Img_r10_c15.tif"

    def __init__(
        self,
        archive_dir: Path,
        unit_of_work: AbstractUnitOfWork,
        handlers: list[HandlerT] = DEFAULT_HANDLERS,
    ):
        super().__init__(patterns=[self.FILE_NAME])

        self.archive_dir = archive_dir
        self.unit_of_work = unit_of_work
        self.handlers = handlers

    def on_created(self, event: FileSystemEvent) -> None:

        base_dto = parse_timestep_dir(Path(event.src_path).parent.parent)

        LOGGER.info("New timestep %s", base_dto.experiment.id)

        archive_path = self.archive_dir / f"{base_dto.experiment.id}.tar"

        data = TimestepDTO(
            experiment_archive_path=archive_path,
            **base_dto.model_dump(by_alias=True),
        )

        for handler in self.handlers:
            handler(data, self.unit_of_work)
