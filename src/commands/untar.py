import logging
import tarfile
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def _should_skip(name: str) -> bool:
    """Проверяет, нужно ли пропустить элемент с каталогом .git."""
    parts = Path(name).parts
    return any(part == ".git" for part in parts)


def _validated_member(name: str) -> Path:
    """Убеждается, что элемент архива не содержит опасных путей."""
    path = Path(name)
    if path.is_absolute():
        raise CommandError(f"untar: unsafe absolute path '{name}'")
    if any(part == ".." for part in path.parts):
        raise CommandError(f"untar: unsafe relative path '{name}'")
    return path


def _top_level_dir(members: list[tarfile.TarInfo]) -> str | None:
    """Возвращает имя общей корневой директории, если она одна."""
    names: set[str] = set()
    for member in members:
        parts = Path(member.name).parts
        if not parts:
            continue
        names.add(parts[0])
        if len(names) > 1:
            return None
    if not names:
        return None

    name = names.pop()
    for member in members:
        parts = Path(member.name).parts
        if parts and parts[0] == name:
            if member.isdir() or len(parts) > 1:
                return name
    return None


def _unique_name(base_dir: Path, basename: str) -> str:
    """Подбирает уникальное имя каталога, добавляя числовой суффикс."""
    candidate = base_dir / basename
    if not candidate.exists():
        return basename
    index = 1
    while True:
        name = f"{basename}-{index}"
        if not (base_dir / name).exists():
            return name
        index += 1


def _preferred_root_name(archive_path: Path) -> str:
    """Определяет желаемое имя каталога по имени архива."""

    name = archive_path.name
    if name.endswith(".tar.gz"):
        return name[:-7]
    if name.endswith(".tgz"):
        return name[:-4]
    if name.endswith(".tar"):
        return name[:-4]
    return archive_path.stem


def run(args: list[str], shell) -> str:
    """Распаковывает TAR.GZ архив в текущий каталог."""
    if len(args) != 1:
        raise CommandError("Usage: untar <archive.tar.gz>")

    archive_path = resolve_path(args[0], shell.cwd)
    if not archive_path.exists():
        raise CommandError(f"untar: '{archive_path}' not found")
    if archive_path.is_dir():
        raise CommandError("untar: target must be a file")

    target_dir = shell.cwd
    try:
        with tarfile.open(archive_path, "r:gz") as tf:
            members = []
            for member in tf.getmembers():
                if _should_skip(member.name):
                    continue
                _validated_member(member.name)
                members.append(member)

            root_dir = _top_level_dir(members)
            strip_levels = 0
            new_root: str | None = None
            output_root: Path = target_dir

            if root_dir is not None:
                existing = target_dir / root_dir
                if existing.exists():
                    preferred = _preferred_root_name(archive_path)
                    new_root = _unique_name(target_dir, preferred)
                    strip_levels = 1
                    output_root = target_dir / new_root
                else:
                    output_root = existing

            adjusted_members: list[tarfile.TarInfo] = []
            for member in members:
                parts = Path(member.name).parts
                if strip_levels and len(parts) >= strip_levels:
                    relative_parts = parts[strip_levels:]
                else:
                    relative_parts = parts
                if new_root is not None:
                    new_name = Path(new_root, *relative_parts)
                else:
                    new_name = Path(*relative_parts)
                member.name = str(new_name)
                adjusted_members.append(member)

            tf.extractall(target_dir, adjusted_members)
        logger.debug(f"untarred {archive_path} to {output_root}")
        return f"Unpacked '{archive_path}' to '{output_root}'"
    except Exception as error:
        logger.exception(f"untar error: {error}")
        raise CommandError(f"untar: error extracting archive: {error}")
