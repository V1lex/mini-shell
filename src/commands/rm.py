import logging
import os
import shutil
from pathlib import Path
from datetime import datetime

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def _move_to_trash(path: Path, trash_root: Path) -> Path:
    """Перемещает объект в корзину и возвращает путь назначения."""
    trash_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    suffix = f"{timestamp}_{os.getpid()}"
    trash_path = trash_root / f"{path.name}.{suffix}"
    shutil.move(str(path), str(trash_path))
    return trash_path


def run(args: list[str], shell) -> str:
    """Удаляет файлы или каталоги, перемещая их в корзину."""
    if not args:
        raise CommandError("Usage: rm [-r] <path>...")

    recursive = False
    targets: list[str] = []

    for arg in args:
        if arg == "-r":
            recursive = True
        elif arg.startswith("-"):
            raise CommandError(f"rm: unsupported option '{arg}'")
        else:
            targets.append(arg)

    if not targets:
        raise CommandError("rm: missing operand")

    messages: list[str] = []

    for raw in targets:
        path = resolve_path(raw, shell.cwd)
        raw_clean = raw.rstrip("/")
        if path == Path("/"):
            raise CommandError("rm: refusing to remove '/'")
        if raw_clean in {"..", "/.."} or path == shell.cwd.parent:
            raise CommandError("rm: refusing to remove '..'")
        if not path.exists():
            raise CommandError(f"rm: '{path}' not found")
        if path.is_dir() and not recursive:
            raise CommandError(f"rm: cannot remove '{path}': is a directory")

        if path.is_dir():
            prompt = f"Remove directory '{path}' recursively? (y/n): "
            answer = input(prompt).strip().lower()
            if answer != "y":
                logger.debug("rm cancelled for directory %s", path)
                continue

        trash_path = _move_to_trash(path, shell.trash_dir)

        shell.push_undo(
            {
                "command": "rm",
                "original": str(path),
                "trash": str(trash_path),
            }
        )

        label = "directory" if trash_path.is_dir() else "file"
        message = f"Removed {label} '{path}'"
        messages.append(message)
        logger.debug("rm moved %s to trash %s", path, trash_path)

    if not messages:
        return "Deletion cancelled"

    return "\n".join(messages)
