from pathlib import Path

from watchfiles import Change


def filter_on_param_file(change: Change, path: str) -> bool:
    path_obj = Path(path)

    is_added = change == Change.added
    is_param_file = path_obj.name == "param.json"

    return is_added and is_param_file
