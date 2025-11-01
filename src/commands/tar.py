import logging
import tarfile
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def _filter_member(member: tarfile.TarInfo) -> tarfile.TarInfo | None:
    """Пропускает служебные каталоги (.git) при архивации."""
    parts = Path(member.name).parts
    if any(part == ".git" for part in parts):
        return None
    return member


def run(args: list[str], shell) -> str:
    """Создаёт TAR.GZ архив из каталога."""
    if len(args) != 2:
        raise CommandError("Usage: tar <folder> <archive.tar.gz>")

    source = resolve_path(args[0], shell.cwd)
    archive_path = resolve_path(args[1], shell.cwd)

    if not source.exists():
        raise CommandError(f"tar: source '{source}' does not exist")
    if not source.is_dir():
        raise CommandError("tar: source must be a directory")

    archive_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(archive_path, "w:gz") as tf:
            tf.add(source, arcname=source.name, filter=_filter_member)
        logger.debug(f"created tar {archive_path} from {source}")
        return f"Created archive '{archive_path}'"
    except Exception as error:
        logger.exception(f"tar error: {error}")
        raise CommandError(f"tar: error creating archive: {error}")
