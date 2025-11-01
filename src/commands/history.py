from .utils import CommandError

DEFAULT_HISTORY_LIMIT = 10


def run(args: list[str], shell) -> str:
    """Выводит последние команды истории (по умолчанию — 10 последних)."""
    all_entries = shell.read_history()
    if args:
        try:
            limit = int(args[0])
        except ValueError as error:
            raise CommandError(
                "history: argument must be an integer") from error
        if limit <= 0:
            raise CommandError("history: argument must be positive")
    else:
        limit = DEFAULT_HISTORY_LIMIT

    entries = all_entries[-limit:]

    if not entries:
        return "History is empty"

    offset = len(all_entries) - len(entries)
    lines = [f"{offset + idx + 1}: {line}" for idx, line in enumerate(entries)]
    return "\n".join(lines)
