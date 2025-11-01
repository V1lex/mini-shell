import logging
from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def run(args: list[str], shell) -> str:
    """Возвращает содержимое указанного файла."""
    if len(args) != 1:
        raise CommandError("Usage: cat <file>")

    file_path = resolve_path(args[0], shell.cwd)

    if not file_path.exists():
        raise CommandError(f"cat: '{file_path}' not found")
    if file_path.is_dir():
        raise CommandError("cat: target must be a file")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="utf-8", errors="ignore")

    logger.debug("cat read %s", file_path)
    return content
