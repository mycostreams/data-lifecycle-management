import os

import sentry_sdk

from .worker import WorkerSettings

__all__ = ("WorkerSettings",)


sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    enable_tracing=True,
)
