"""Celery application."""

from celery import Celery, signals
from celery.utils.log import get_task_logger

from prince_archiver.config import get_settings
from prince_archiver.logging import configure_logging

LOGGER = get_task_logger(__name__)

app = Celery("worker")

app.autodiscover_tasks([__name__])
app.config_from_object(get_settings(), namespace="CELERY")


@signals.worker_ready.connect
def on_worker_ready(**_):
    LOGGER.info("Ready for action: %s", __name__)


@signals.setup_logging.connect
def setup_logging(**_):
    configure_logging()
