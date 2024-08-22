from pathlib import Path
from typing import Any

from sqlalchemy import Dialect, String, TypeDecorator


class PathType(TypeDecorator):
    """
    Custom type used to convert
    """

    impl = String

    def process_bind_param(self, value: Any | None, dialect: Dialect) -> Any:
        if isinstance(value, Path):
            value = value.as_posix()
        return value

    def process_result_value(self, value: Any | None, dialect: Dialect) -> Any | None:
        if isinstance(value, str):
            return Path(value)
        return value
