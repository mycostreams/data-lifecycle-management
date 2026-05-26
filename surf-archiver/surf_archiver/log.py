import logging
import logging.handlers
from pathlib import Path
from uuid import UUID

import structlog


def _build_pre_chain(extra_processors=None):
    chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    if extra_processors:
        chain.extend(extra_processors)
    return chain


def _apply_structlog(pre_chain):
    structlog.configure(
        processors=pre_chain
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_logging(job_id: UUID, file: Path):
    if logging.getLogger().handlers:
        return

    file.parent.mkdir(exist_ok=True, parents=True)

    pre_chain = _build_pre_chain(
        [structlog.processors.CallsiteParameterAdder([])]
        if False
        else None,
    )
    _apply_structlog(pre_chain)

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=pre_chain,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.handlers.RotatingFileHandler(
        str(file), mode="a", backupCount=3
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    logging.getLogger("surf_archiver").setLevel(logging.DEBUG)


def configure_remote_logging():
    if logging.getLogger().handlers:
        return

    pre_chain = _build_pre_chain()
    _apply_structlog(pre_chain)

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=pre_chain,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    for name in ("surf_archiver", "arq"):
        logging.getLogger(name).setLevel(logging.DEBUG)
