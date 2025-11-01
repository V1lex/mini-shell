import pytest

from src.commands import cat
from src.commands.utils import CommandError


def test_cat_returns_file_contents(fs, shell):
    path = shell.cwd / "story.txt"
    fs.create_file(str(path), contents="line one\nline two")

    result = cat.run([path.name], shell)

    assert result == "line one\nline two"


def test_cat_raises_for_missing_file(shell):
    with pytest.raises(CommandError):
        cat.run(["missing.txt"], shell)


def test_cat_rejects_directory(fs, shell):
    directory = shell.cwd / "docs"
    fs.create_dir(str(directory))

    with pytest.raises(CommandError):
        cat.run([directory.name], shell)


def test_cat_ignores_invalid_utf8(fs, shell):
    path = shell.cwd / "binary.dat"
    fs.create_file(str(path), contents=b"\xff\xfe\xfa")

    output = cat.run([path.name], shell)

    assert output == ""


def test_cat_requires_single_argument(shell):
    with pytest.raises(CommandError):
        cat.run([], shell)
