import logging
import logging.config
from pathlib import Path
from uuid import UUID


def configure_logging(job_id: UUID, file: Path):
    file.parent.mkdir(exist_ok=True, parents=True)

    log_format = f"[{job_id}] %(asctime)s - %(levelname)s - %(name)s - %(message)s"

    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "simple": {
                    "format": log_format,
                },
            },
            "handlers": {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "simple",
                    "filename": str(file),
                    "level": "INFO",
                    "mode": "a",
                    "backupCount": 3,
                }
            },
            "loggers": {
                "surf_archiver": {
                    "level": "DEBUG",
                    "handlers": ["file"],
                }
            },
        }
    )


def configure_remote_logging():
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "surf_archiver": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "arq": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )
