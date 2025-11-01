import logging
import shutil
import zipfile
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def _should_skip(name: str) -> bool:
    """Возвращает True, если путь относится к каталогу .git."""
    parts = Path(name).parts
    return any(part == ".git" for part in parts)


def _validated_path(name: str) -> Path:
    """Проверяет, что путь внутри архива безопасен для извлечения."""
    path = Path(name)
    if path.is_absolute():
        raise CommandError(f"unzip: unsafe absolute path '{name}'")
    if any(part == ".." for part in path.parts):
        raise CommandError(f"unzip: unsafe relative path '{name}'")
    return path


def _top_level_dir(infos: list[zipfile.ZipInfo]) -> str | None:
    """Определяет общую верхнюю директорию, если она присутствует одна."""
    names: set[str] = set()
    for info in infos:
        parts = Path(info.filename).parts
        if not parts:
            continue
        names.add(parts[0])
        if len(names) > 1:
            return None
    if not names:
        return None

    name = names.pop()
    for info in infos:
        parts = Path(info.filename).parts
        if parts and parts[0] == name:
            if info.is_dir() or len(parts) > 1:
                return name
    return None


def _unique_name(base_dir: Path, basename: str) -> str:
    """Возвращает уникальное имя каталога, добавляя числовой суффикс."""
    candidate = base_dir / basename
    if not candidate.exists():
        return basename
    index = 1
    while True:
        name = f"{basename}-{index}"
        if not (base_dir / name).exists():
            return name
        index += 1


def run(args: list[str], shell) -> str:
    """Распаковывает ZIP-архив в текущий каталог."""
    if len(args) != 1:
        raise CommandError("Usage: unzip <archive.zip>")

    archive_path = resolve_path(args[0], shell.cwd)
    if not archive_path.exists():
        raise CommandError(f"unzip: '{archive_path}' not found")
    if archive_path.is_dir():
        raise CommandError("unzip: target must be a file")

    target_dir = shell.cwd
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            filtered: list[zipfile.ZipInfo] = []
            for info in zf.infolist():
                if _should_skip(info.filename):
                    continue
                _validated_path(info.filename)
                filtered.append(info)

            root_dir = _top_level_dir(filtered)
            strip_levels = 0
            base_target = target_dir
            output_root: Path = target_dir

            if root_dir is not None:
                existing = target_dir / root_dir
                if existing.exists():
                    preferred = archive_path.stem
                    new_root = _unique_name(target_dir, preferred)
                    base_target = target_dir / new_root
                    base_target.mkdir(parents=True, exist_ok=True)
                    strip_levels = 1
                    output_root = base_target
                else:
                    output_root = existing

            for info in filtered:
                parts = Path(info.filename).parts
                if strip_levels and len(parts) >= strip_levels:
                    relative_parts = parts[strip_levels:]
                else:
                    relative_parts = parts
                relative = Path(*relative_parts)
                destination = base_target / relative

                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
        logger.debug(f"unzipped {archive_path} to {output_root}")
        return f"Unpacked '{archive_path}' to '{output_root}'"
    except Exception as error:
        logger.exception(f"unzip error: {error}")
        raise CommandError(f"unzip: error extracting archive: {error}")
