"""Celery application."""

from celery import Celery, signals
from celery.utils.log import get_task_logger

from prince_archiver.config import get_settings

LOGGER = get_task_logger(__name__)

app = Celery("worker")

app.autodiscover_tasks([__name__])
app.config_from_object(get_settings(), namespace="CELERY")


@signals.worker_ready.connect
def on_worker_ready(**_):
    LOGGER.info("@@@@@@ %s", __name__)
