import logging
import os
import stat
from datetime import datetime
from pathlib import Path

from .utils import CommandError, resolve_path

logger = logging.getLogger("shell")


def run(args: list[str], shell) -> str:
    """Выводит содержимое каталога и/или сведения о файлах."""
    long_format = False
    targets: list[str] = []

    for arg in args:
        if arg == "-l":
            long_format = True
        elif arg.startswith("-"):
            raise CommandError(f"ls: unsupported option '{arg}'")
        else:
            targets.append(arg)

    if not targets:
        resolved = [shell.cwd]
        display = ["."]
    else:
        resolved = [resolve_path(item, shell.cwd) for item in targets]
        display = targets

    sections: list[str] = []
    multiple = len(resolved) > 1

    for index, path in enumerate(resolved):
        raw_name = display[index]
        if not path.exists() and not path.is_symlink():
            raise CommandError(
                f"ls: cannot access '{raw_name}': No such file or directory")

        if path.is_dir():
            listing = _list_directory(path, long_format)
            if multiple:
                header = raw_name if raw_name != "." else str(path)
                sections.append(f"{header}:\n{listing}" if listing else f"{header}:")
            else:
                sections.append(listing)
        else:
            name = raw_name if targets else path.name
            sections.append(_format_entry(path, long_format, name))

    result = "\n\n".join(part for part in sections if part is not None)
    logger.debug("ls executed with args: %s", args)
    return result


def _list_directory(path: Path, long_format: bool) -> str:
    """Формирует вывод по содержимому каталога."""
    try:
        entries = sorted(
            (item for item in path.iterdir() if not item.name.startswith(".")),
            key=lambda item: item.name.casefold(),
        )
    except PermissionError as error:
        raise CommandError(
            f"ls: cannot open directory '{path}': {error}") from error

    formatted = [_format_entry(entry, long_format) for entry in entries]
    return "\n".join(formatted)


def _format_entry(path: Path, long_format: bool,
                  display_name: str | None = None) -> str:
    """Возвращает строку для элемента списка."""
    name = display_name if display_name is not None else path.name
    if long_format:
        return _format_long_entry(path, name)
    return name


def _format_long_entry(path: Path, display_name: str) -> str:
    """Возвращает подробную строку в стиле `ls -l`."""
    stats = path.lstat()
    mode = stat.filemode(stats.st_mode)
    size = stats.st_size
    modified = datetime.fromtimestamp(stats.st_mtime)
    month_names = {
        1: "янв.",
        2: "фев.",
        3: "мар.",
        4: "апр.",
        5: "май",
        6: "июн.",
        7: "июл.",
        8: "авг.",
        9: "сент.",
        10: "окт.",
        11: "нояб.",
        12: "дек.",
    }
    month = month_names.get(modified.month, f"{modified.month:02d}")
    date_text = (
        f"{modified.day} {month} "
        f"{modified.hour:02d}:{modified.minute:02d}"
    )

    name = display_name
    if path.is_symlink():
        try:
            target = os.readlink(path)
        except OSError:
            target = "?"
        name = f"{display_name} -> {target}"

    return f"{mode} {size:>8} {date_text} {name}"
