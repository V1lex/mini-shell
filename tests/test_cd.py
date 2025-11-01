import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.commands import cd
from src.commands.utils import CommandError


def test_cd_changes_directory(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    target = home_dir / "projects"
    fs.create_dir(str(target))

    cd.run(["projects"], shell_instance)

    assert shell_instance.cwd == target


def test_cd_without_arguments_returns_home(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    other = home_dir / "tmp"
    fs.create_dir(str(other))
    shell_instance.cwd = other

    cd.run([], shell_instance)

    assert shell_instance.cwd == home_dir


def test_cd_fails_for_missing_directory(shell_instance) -> None:
    with pytest.raises(CommandError) as error:
        cd.run(["absent"], shell_instance)

    assert "No such file or directory" in str(error.value)


def test_cd_fails_for_file_instead_directory(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    file_path = home_dir / "file.txt"
    fs.create_file(str(file_path), contents="content")

    with pytest.raises(CommandError) as error:
        cd.run(["file.txt"], shell_instance)

    assert "Not a directory" in str(error.value)
