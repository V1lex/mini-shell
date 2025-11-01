import pytest

from src.commands import mv
from src.commands.utils import CommandError


def test_mv_renames_file(fs, shell):
    source = shell.cwd / "notes.txt"
    destination = shell.cwd / "notes_old.txt"
    fs.create_file(str(source), contents="data")

    message = mv.run([source.name, destination.name], shell)

    assert not source.exists()
    assert destination.read_text(encoding="utf-8") == "data"
    assert message == f"Moved '{source}' -> '{destination}'"
    assert shell.undo_stack[-1] == {
        "command": "mv",
        "source": str(source),
        "destination": str(destination),
    }


def test_mv_moves_into_directory(fs, shell):
    source = shell.cwd / "photo.jpg"
    target_dir = shell.cwd / "pictures"
    fs.create_file(str(source), contents="jpeg")
    fs.create_dir(str(target_dir))

    mv.run([source.name, target_dir.name], shell)

    destination = target_dir / source.name
    assert destination.exists()
    assert not source.exists()


def test_mv_fails_when_source_missing(shell):
    with pytest.raises(CommandError):
        mv.run(["absent.txt", "new.txt"], shell)
