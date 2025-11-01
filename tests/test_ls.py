from datetime import datetime

import pytest

from src.commands import ls
from src.commands.utils import CommandError


def test_ls_lists_directory_contents(fs, shell):
    fs.create_file(str(shell.cwd / "alpha.txt"), contents="A")
    fs.create_file(str(shell.cwd / "beta.txt"), contents="B")
    fs.create_dir(str(shell.cwd / "notes"))

    result = ls.run([], shell)

    assert result.splitlines() == ["alpha.txt", "beta.txt", "notes"]


def test_ls_long_format_includes_metadata(fs, shell):
    path = shell.cwd / "report.txt"
    fs.create_file(str(path), contents="data")
    timestamp = datetime(2024, 1, 15, 8, 5).timestamp()
    fs.utime(str(path), (timestamp, timestamp))

    output = ls.run(["-l"], shell)
    lines = output.splitlines()

    assert len(lines) == 1
    parts = lines[0].split()
    assert parts[0].startswith("-")
    assert parts[1] == "4"
    assert parts[3] == "янв."
    assert parts[-1] == "report.txt"


def test_ls_raises_for_missing_path(shell):
    with pytest.raises(CommandError):
        ls.run(["missing.txt"], shell)


def test_ls_rejects_unknown_option(shell):
    with pytest.raises(CommandError):
        ls.run(["-x"], shell)


def test_ls_adds_headers_for_multiple_targets(fs, shell):
    first = shell.cwd / "dir1"
    second = shell.cwd / "dir2"
    fs.create_dir(str(first))
    fs.create_dir(str(second))
    fs.create_file(str(first / "a.txt"), contents="A")
    fs.create_file(str(second / "b.txt"), contents="B")

    result = ls.run([first.name, second.name], shell)
    sections = result.split("\n\n")

    assert any(line.startswith(f"{first.name}:") for line in sections)
    assert any(line.startswith(f"{second.name}:") for line in sections)
