from celery import Task

from prince_archiver.config import Settings, get_settings


class AbstractTask:

    def __init__(self, *, _settings: Settings | None = None):
        self.settings = _settings or get_settings()


class ConcreteTask(AbstractTask, Task):
    pass
