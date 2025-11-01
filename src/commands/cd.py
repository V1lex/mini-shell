import logging
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def run(args: list[str], shell_state) -> str:
    """Меняет текущий каталог оболочки."""
    if not args:
        new = Path.home()
    else:
        new = resolve_path(args[0], shell_state.cwd)

    if not new.exists():
        raise CommandError(f"cd: {new}: No such file or directory")
    if not new.is_dir():
        raise CommandError(f"cd: {new}: Not a directory")

    shell_state.cwd = new
    logger.debug(f"Changed cwd to {new}")
    return ""
