from pathlib import Path

import pytest

from src.commands import cd
from src.commands.utils import CommandError


def test_cd_changes_to_existing_directory(fs, shell):
    target = shell.cwd / "projects"
    fs.create_dir(str(target))

    cd.run([target.name], shell)

    assert shell.cwd == target


def test_cd_raises_for_missing_path(shell):
    with pytest.raises(CommandError):
        cd.run(["unknown"], shell)


def test_cd_rejects_file_target(fs, shell):
    file_path = shell.cwd / "notes.txt"
    fs.create_file(str(file_path), contents="data")

    with pytest.raises(CommandError):
        cd.run([file_path.name], shell)


def test_cd_without_arguments_moves_to_home(fs, shell):
    home_path = Path.home()
    fs.create_dir(str(home_path))

    cd.run([], shell)

    assert shell.cwd == home_path


def test_cd_goes_to_home_with_tilde(fs, shell, monkeypatch):
    home = Path("/home/custom")
    fs.create_dir(str(home))
    monkeypatch.setenv("HOME", str(home))

    cd.run(["~"], shell)

    assert shell.cwd == home.resolve()


def test_cd_goes_one_level_up(fs, shell):
    parent = shell.cwd.parent

    cd.run([".."], shell)

    assert shell.cwd == parent
