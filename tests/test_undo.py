import pytest

from src.commands import undo
from src.commands.utils import CommandError


def test_undo_reverses_copy(fs, shell):
    target = shell.cwd / "copied.txt"
    fs.create_file(str(target), contents="data")
    shell.push_undo({"command": "cp", "target": str(target)})

    message = undo.run([], shell)

    assert not target.exists()
    assert message == f"Undo: removed '{target}'"


def test_undo_restores_move(fs, shell):
    original = shell.cwd / "notes.txt"
    destination = shell.cwd / "archive" / "notes.txt"
    fs.create_dir(str(destination.parent))
    fs.create_file(str(destination), contents="memo")
    shell.push_undo(
        {
            "command": "mv",
            "source": str(original),
            "destination": str(destination),
        }
    )

    result = undo.run([], shell)

    assert original.exists()
    assert not destination.exists()
    assert original.read_text(encoding="utf-8") == "memo"
    assert result == f"Undo: moved back to '{original}'"


def test_undo_restores_deleted_file(fs, shell):
    original = shell.cwd / "report.txt"
    trash = shell.trash_dir / "report.txt.1"
    fs.create_file(str(trash), contents="draft")
    shell.push_undo(
        {
            "command": "rm",
            "original": str(original),
            "trash": str(trash),
        }
    )

    message = undo.run([], shell)

    assert original.exists()
    assert not trash.exists()
    assert original.read_text(encoding="utf-8") == "draft"
    assert message == f"Undo: restored '{original}'"


def test_undo_requires_pending_action(shell):
    with pytest.raises(CommandError):
        undo.run([], shell)


def test_undo_restores_action_on_failure(fs, shell):
    missing_target = shell.cwd / "ghost.txt"
    shell.push_undo({"command": "cp", "target": str(missing_target)})

    with pytest.raises(CommandError):
        undo.run([], shell)

    assert shell.undo_stack[-1]["command"] == "cp"


def test_undo_rejects_extra_arguments(fs, shell):
    shell.push_undo({"command": "cp", "target": str(shell.cwd / "file.txt")})

    with pytest.raises(CommandError):
        undo.run(["unexpected"], shell)


def test_undo_handles_unsupported_action(shell):
    shell.push_undo({"command": "unknown"})

    with pytest.raises(CommandError):
        undo.run([], shell)

    assert shell.undo_stack[-1]["command"] == "unknown"
