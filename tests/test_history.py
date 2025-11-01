import pytest

from src.commands import history
from src.commands.utils import CommandError


def test_history_returns_last_ten_entries(shell):
    shell.history_entries = [f"cmd {index}" for index in range(1, 13)]

    output = history.run([], shell)

    lines = output.splitlines()
    assert len(lines) == 10
    assert lines[0] == "3: cmd 3"
    assert lines[-1] == "12: cmd 12"


def test_history_accepts_custom_limit(shell):
    shell.history_entries = ["alpha", "beta", "gamma"]

    result = history.run(["2"], shell)

    assert result.splitlines() == ["2: beta", "3: gamma"]


def test_history_reports_empty_history(shell):
    shell.history_entries = []

    assert history.run([], shell) == "History is empty"


def test_history_requires_positive_integer(shell):
    shell.history_entries = ["one"]

    with pytest.raises(CommandError):
        history.run(["0"], shell)


def test_history_rejects_non_numeric_argument(shell):
    shell.history_entries = ["entry"]

    with pytest.raises(CommandError):
        history.run(["abc"], shell)
