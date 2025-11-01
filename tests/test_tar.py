import tarfile
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.commands import tar
from src.commands.utils import CommandError


def _list_tar_members(archive: Path) -> set[str]:
    with tarfile.open(archive, "r:gz") as tf:
        return set(tf.getnames())


def test_tar_creates_archive_excluding_git(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    source = home_dir / "project"
    fs.create_dir(str(source))
    fs.create_file(str(source / "file.txt"), contents="data")
    git_dir = source / ".git"
    fs.create_dir(str(git_dir))
    fs.create_file(str(git_dir / "config"), contents="[core]")

    archive = home_dir / "project.tar.gz"
    message = tar.run(["project", "project.tar.gz"], shell_instance)

    assert "Created archive" in message
    assert archive.exists()
    members = _list_tar_members(archive)
    assert "project/file.txt" in members
    assert all(".git" not in name for name in members)


def test_tar_requires_existing_directory(shell_instance) -> None:
    with pytest.raises(CommandError):
        tar.run(["missing", "archive.tar.gz"], shell_instance)


def test_tar_rejects_non_directory_source(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    fs.create_file(str(home_dir / "file.txt"), contents="data")

    with pytest.raises(CommandError):
        tar.run(["file.txt", "archive.tar.gz"], shell_instance)
