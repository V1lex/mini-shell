import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.commands import history
from src.commands.history import DEFAULT_HISTORY_LIMIT
from src.commands.utils import CommandError


def _write_history(fs: FakeFilesystem, shell_instance, lines: list[str]) -> None:
    content = "\n".join(lines)
    history_path = shell_instance.history_file
    if fs.exists(str(history_path)):
        fs.remove_object(str(history_path))
    history_path.write_text(
        content + ("\n" if lines else ""), encoding="utf-8"
    )


def test_history_returns_last_entries_by_default(
    fs: FakeFilesystem,
    shell_instance,
) -> None:
    commands = [f"cmd {index}" for index in range(1, DEFAULT_HISTORY_LIMIT + 3)]
    _write_history(fs, shell_instance, commands)

    result = history.run([], shell_instance)

    tail = commands[-DEFAULT_HISTORY_LIMIT:]
    offset = len(commands) - len(tail)
    expected = [
        f"{offset + idx + 1}: {line}"
        for idx, line in enumerate(tail)
    ]
    assert result.splitlines() == expected


def test_history_handles_custom_limit(
    fs: FakeFilesystem,
    shell_instance,
) -> None:
    commands = [f"cmd {index}" for index in range(1, 6)]
    _write_history(fs, shell_instance, commands)

    result = history.run(["3"], shell_instance)

    assert result.splitlines() == [
        "3: cmd 3",
        "4: cmd 4",
        "5: cmd 5",
    ]


def test_history_reports_empty(
    fs: FakeFilesystem,
    shell_instance,
) -> None:
    _write_history(fs, shell_instance, [])

    result = history.run([], shell_instance)

    assert result == "History is empty"


def test_history_rejects_non_integer_argument(shell_instance) -> None:
    with pytest.raises(CommandError):
        history.run(["oops"], shell_instance)


def test_history_rejects_non_positive_argument(shell_instance) -> None:
    with pytest.raises(CommandError):
        history.run(["0"], shell_instance)
