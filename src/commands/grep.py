import logging
import re
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def run(args, shell) -> str:
    """Ищет строки, соответствующие шаблону, в файлах."""
    if not args:
        raise CommandError("Usage: grep [-r] [-i] <pattern> [path]")

    recursive = False
    ignore_case = False
    index = 0

    while index < len(args) and args[index].startswith("-") and len(args[index]) > 1:
        option = args[index][1:]
        for flag in option:
            if flag == "r":
                recursive = True
            elif flag == "i":
                ignore_case = True
            else:
                raise CommandError(f"grep: unsupported option '-{flag}'")
        index += 1

    remaining = args[index:]
    if not remaining:
        raise CommandError("Usage: grep [-r] [-i] <pattern> [path]")

    pattern_text = remaining[0]
    if len(remaining) > 2:
        raise CommandError("Usage: grep [-r] [-i] <pattern> [path]")

    path_arg = remaining[1] if len(remaining) == 2 else None
    display_base = path_arg if path_arg is not None else "."

    if path_arg is None:
        if not recursive:
            raise CommandError("Usage: grep [-r] [-i] <pattern> [path]")
        target = shell.cwd
    else:
        target = resolve_path(path_arg, shell.cwd)

    if not target.exists():
        raise CommandError(f"grep: path '{target}' not found")

    if target.is_dir() and not recursive:
        raise CommandError("grep: -r is required when target is a directory")

    flags = re.IGNORECASE if ignore_case else 0
    try:
        pattern = re.compile(pattern_text, flags)
    except re.error as error:
        raise CommandError(f"grep: invalid pattern: {error}") from error

    files = _iter_files(target, recursive)
    matches = []
    show_path = recursive or len(files) > 1 or target.is_dir()

    for file_path in files:
        try:
            for line in file_path.read_text(encoding="utf-8").splitlines():
                if pattern.search(line):
                    if show_path:
                        display_path = _format_path(file_path, shell.cwd, target, display_base)
                        matches.append(f"{display_path}:{line}")
                    else:
                        matches.append(line)
        except Exception as error:
            logger.error(f"grep: failed to read {file_path}: {error}")

    if not matches:
        return "no matches found"
    return "\n".join(matches)


def _iter_files(path, recursive):
    """Возвращает список файлов для поиска."""
    if path.is_file():
        return [path]
    if not recursive:
        raise CommandError("grep: -r is required when target is a directory")
    return [p for p in path.rglob("*") if p.is_file()]


def _format_path(file_path: Path, cwd: Path, target: Path, base_display: str) -> str:
    """Возвращает путь к файлу, используя базовый аргумент или относительный путь."""
    if not target.is_file():
        try:
            relative_to_target = file_path.relative_to(target).as_posix()
            prefix = base_display.rstrip("/")
            if not relative_to_target:
                return prefix or "."
            if prefix in {"", "."}:
                return f"./{relative_to_target}"
            return f"{prefix}/{relative_to_target}"
        except ValueError:
            pass
    else:
        if file_path == target:
            return base_display

    try:
        relative = file_path.relative_to(cwd)
        rel_text = relative.as_posix()
        return rel_text or "."
    except ValueError:
        return str(file_path)
