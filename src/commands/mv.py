import logging
import shutil
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def _final_destination(source: Path, destination: Path) -> Path:
    """Определяет фактический путь назначения."""
    if destination.exists() and destination.is_dir():
        return destination / source.name
    return destination


def run(args: list[str], shell) -> str:
    """Перемещает или переименовывает файл/каталог."""
    if len(args) != 2:
        raise CommandError("Usage: mv <source> <destination>")

    source = resolve_path(args[0], shell.cwd)
    if not source.exists():
        raise CommandError(f"mv: source '{source}' not found")

    destination_raw = resolve_path(args[1], shell.cwd)
    destination = _final_destination(source, destination_raw)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.resolve() == destination.resolve():
        raise CommandError("mv: source and destination are the same")

    try:
        shutil.move(str(source), str(destination))
    except Exception as error:
        logger.exception("mv failed: %s", error)
        raise CommandError(f"mv: failed to move: {error}") from error

    shell.push_undo(
        {
            "command": "mv",
            "source": str(source),
            "destination": str(destination),
        }
    )
    logger.debug("mv %s -> %s", source, destination)
    return f"Moved '{source}' -> '{destination}'"
