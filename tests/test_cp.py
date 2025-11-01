import pytest

from src.commands import cp
from src.commands.utils import CommandError


def test_cp_copies_file_into_new_path(fs, shell):
    source = shell.cwd / "source.txt"
    destination = shell.cwd / "copy.txt"
    fs.create_file(str(source), contents="hello")

    message = cp.run([source.name, destination.name], shell)

    assert destination.read_text(encoding="utf-8") == "hello"
    assert message == f"Copied file '{source}' -> '{destination}'"
    assert shell.undo_stack[-1] == {"command": "cp", "target": str(destination)}


def test_cp_requires_recursive_flag_for_directory(fs, shell):
    directory = shell.cwd / "docs"
    fs.create_dir(str(directory))

    with pytest.raises(CommandError):
        cp.run([directory.name, "backup"], shell)


def test_cp_copies_directory_recursively(fs, shell):
    source_dir = shell.cwd / "project"
    fs.create_dir(str(source_dir))
    fs.create_file(str(source_dir / "main.py"), contents="print('ok')")

    destination_dir = shell.cwd / "project_copy"
    result = cp.run(["-r", source_dir.name, destination_dir.name], shell)

    copied_file = destination_dir / "main.py"
    assert copied_file.exists()
    assert copied_file.read_text(encoding="utf-8") == "print('ok')"
    assert result == f"Copied directory '{source_dir}' -> '{destination_dir}'"


def test_cp_places_file_inside_existing_directory(fs, shell):
    source = shell.cwd / "image.png"
    target_dir = shell.cwd / "assets"
    fs.create_file(str(source), contents="png")
    fs.create_dir(str(target_dir))

    cp.run([source.name, target_dir.name], shell)

    destination = target_dir / source.name
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "png"


def test_cp_rejects_unknown_option(shell):
    with pytest.raises(CommandError):
        cp.run(["-x", "a", "b"], shell)


def test_cp_requires_two_positional_arguments(shell):
    with pytest.raises(CommandError):
        cp.run(["file"], shell)


def test_cp_raises_when_source_missing(shell):
    with pytest.raises(CommandError):
        cp.run(["missing.txt", "dest.txt"], shell)
