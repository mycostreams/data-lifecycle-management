import logging
import logging.config
from pathlib import Path

import yaml


def configure_logging():
    file = Path(__file__).parent / "logging.yml"
    logging.config.dictConfig(yaml.safe_load(file.read_text()))
