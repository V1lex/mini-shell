from pathlib import Path
import os


class CommandError(Exception):
    """Исключение для предсказуемых ошибок команд."""


def resolve_path(path_str: str, cwd: Path) -> Path:
    """Возвращает абсолютный путь, учитывая ~ и относительные сегменты."""
    if path_str.startswith("~"):
        return Path(os.path.expanduser(path_str)).resolve()
    path = Path(path_str)
    if path.is_absolute():
        return path.resolve()
    return (cwd / path).resolve()
