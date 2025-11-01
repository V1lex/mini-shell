import logging
import zipfile
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def _should_skip(path: Path, source: Path) -> bool:
    """Возвращает True, если элемент попадает в служебный каталог .git."""
    if path == source:
        return False
    try:
        relative = path.relative_to(source)
    except ValueError:
        return False
    return any(part == ".git" for part in relative.parts)


def run(args: list[str], shell) -> str:
    """Создаёт ZIP-архив из указанного каталога."""
    if len(args) != 2:
        raise CommandError("Usage: zip <folder> <archive.zip>")

    source = resolve_path(args[0], shell.cwd)
    archive_path = resolve_path(args[1], shell.cwd)

    if not source.exists():
        raise CommandError(f"zip: source '{source}' does not exist")
    if not source.is_dir():
        raise CommandError("zip: source must be a directory")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(
            archive_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zf:
            zf.write(source, source.name)
            for item in source.rglob("*"):
                if _should_skip(item, source):
                    continue
                arcname = Path(source.name) / item.relative_to(source)
                zf.write(item, str(arcname))
        logger.debug(f"created zip {archive_path} from {source}")
        return f"Created archive '{archive_path}'"
    except Exception as error:
        logger.exception(f"zip error: {error}")
        raise CommandError(f"zip: error creating archive: {error}")
