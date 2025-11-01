import pytest

from src.commands import rm
from src.commands.utils import CommandError


def test_rm_moves_file_to_trash(fs, shell):
    target = shell.cwd / "obsolete.txt"
    fs.create_file(str(target), contents="old data")

    message = rm.run([target.name], shell)

    assert message == f"Removed file '{target}'"
    assert not target.exists()
    trash_items = list(shell.trash_dir.iterdir())
    assert len(trash_items) == 1
    trash_file = trash_items[0]
    assert trash_file.read_text(encoding="utf-8") == "old data"
    assert shell.undo_stack[-1] == {
        "command": "rm",
        "original": str(target),
        "trash": str(trash_file),
    }


def test_rm_requires_recursive_flag_for_directory(fs, shell):
    directory = shell.cwd / "tmp"
    fs.create_dir(str(directory))

    with pytest.raises(CommandError):
        rm.run([directory.name], shell)


def test_rm_removes_directory_recursively(fs, shell, monkeypatch):
    directory = shell.cwd / "logs"
    fs.create_dir(str(directory))
    fs.create_file(str(directory / "latest.log"), contents="entry")
    monkeypatch.setattr("builtins.input", lambda _: "y")

    output = rm.run(["-r", directory.name], shell)

    assert "Removed directory" in output
    assert not directory.exists()
    trash_contents = list(shell.trash_dir.iterdir())
    assert len(trash_contents) == 1
    trash_dir = trash_contents[0]
    assert (trash_dir / "latest.log").exists()


def test_rm_cancels_when_user_declines(fs, shell, monkeypatch):
    directory = shell.cwd / "archive"
    fs.create_dir(str(directory))
    monkeypatch.setattr("builtins.input", lambda _: "n")

    result = rm.run(["-r", directory.name], shell)

    assert result == "Deletion cancelled"
    assert directory.exists()


def test_rm_requires_operands(shell):
    with pytest.raises(CommandError):
        rm.run([], shell)


def test_rm_rejects_unknown_option(shell):
    with pytest.raises(CommandError):
        rm.run(["-z", "file"], shell)


def test_rm_forbids_root(shell):
    with pytest.raises(CommandError):
        rm.run(["/"], shell)


def test_rm_forbids_parent(shell):
    with pytest.raises(CommandError):
        rm.run([".."], shell)
