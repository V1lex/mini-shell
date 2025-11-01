import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.commands import undo
from src.commands.utils import CommandError


def test_undo_reverts_copy(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    copied = home_dir / "copy.txt"
    fs.create_file(str(copied), contents="data")
    shell_instance.push_undo({"command": "cp", "target": str(copied)})

    result = undo.run([], shell_instance)

    assert result == f"Undo: removed '{copied}'"
    assert not copied.exists()


def test_undo_reverts_move(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    source = home_dir / "original.txt"
    destination = home_dir / "moved.txt"
    fs.create_file(str(destination), contents="payload")
    shell_instance.push_undo(
        {
            "command": "mv",
            "source": str(source),
            "destination": str(destination),
        }
    )

    result = undo.run([], shell_instance)

    assert result == f"Undo: moved back to '{source}'"
    assert source.exists()
    assert source.read_text() == "payload"
    assert not destination.exists()


def test_undo_reverts_remove(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    original = home_dir / "file.txt"
    trash = shell_instance.trash_dir / "file.txt.trash"
    fs.makedirs(str(shell_instance.trash_dir), exist_ok=True)
    fs.create_file(str(trash), contents="deleted")
    shell_instance.push_undo(
        {
            "command": "rm",
            "original": str(original),
            "trash": str(trash),
        }
    )

    result = undo.run([], shell_instance)

    assert result == f"Undo: restored '{original}'"
    assert original.exists()
    assert original.read_text() == "deleted"
    assert not trash.exists()


def test_undo_without_actions_fails(shell_instance) -> None:
    with pytest.raises(CommandError):
        undo.run([], shell_instance)


def test_undo_unknown_action_restored(
    shell_instance,
) -> None:
    action = {"command": "unknown"}
    shell_instance.push_undo(action)

    with pytest.raises(CommandError):
        undo.run([], shell_instance)

    assert shell_instance.undo_stack[-1] is action


def test_undo_copy_missing_target_put_back(
    shell_instance,
    home_dir,
) -> None:
    target = home_dir / "lost.txt"
    action = {"command": "cp", "target": str(target)}
    shell_instance.push_undo(action)

    with pytest.raises(CommandError):
        undo.run([], shell_instance)

    assert shell_instance.undo_stack[-1] is action


def test_undo_rejects_arguments(shell_instance) -> None:
    shell_instance.push_undo({"command": "cp", "target": "/tmp/file"})

    with pytest.raises(CommandError):
        undo.run(["extra"], shell_instance)

    assert shell_instance.undo_stack


def test_undo_repushes_action_on_failure(shell_instance) -> None:
    action = {"command": "cp", "target": "/tmp/missing.txt"}
    shell_instance.push_undo(action)

    with pytest.raises(CommandError):
        undo.run([], shell_instance)

    assert shell_instance.undo_stack[-1] is action
