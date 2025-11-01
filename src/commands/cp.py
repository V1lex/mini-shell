import logging
import shutil
from pathlib import Path
from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def _resolve_destination(source: Path, raw_destination: Path) -> Path:
    """Возвращает итоговый путь копирования с учётом каталогов."""
    if raw_destination.exists() and raw_destination.is_dir():
        return raw_destination / source.name
    return raw_destination


def run(args: list[str], shell) -> str:
    """Копирует файл или каталог, поддерживая ключ -r."""
    recursive = False
    positional: list[str] = []

    for arg in args:
        if arg == "-r":
            recursive = True
        elif arg.startswith("-"):
            raise CommandError(f"cp: unsupported option '{arg}'")
        else:
            positional.append(arg)

    if len(positional) != 2:
        raise CommandError("Usage: cp [-r] <source> <destination>")

    source = resolve_path(positional[0], shell.cwd)
    destination_raw = resolve_path(positional[1], shell.cwd)

    if not source.exists():
        raise CommandError(f"cp: source '{source}' not found")
    if source.is_dir() and not recursive:
        raise CommandError("cp: -r required to copy directories")

    destination = _resolve_destination(source, destination_raw)
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
            kind = "directory"
        else:
            shutil.copy2(source, destination)
            kind = "file"
    except Exception as error:
        logger.exception("cp failed: %s", error)
        raise CommandError(f"cp: failed to copy: {error}") from error

    shell.push_undo({"command": "cp", "target": str(destination)})
    logger.debug("cp %s -> %s", source, destination)
    return f"Copied {kind} '{source}' -> '{destination}'"
