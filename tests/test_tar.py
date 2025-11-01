import tarfile

import pytest

from src.commands import tar
from src.commands.utils import CommandError


def test_tar_creates_archive_without_git(fs, shell):
    source = shell.cwd / "docs"
    fs.create_dir(str(source))
    fs.create_file(str(source / "readme.txt"), contents="hello")
    fs.create_dir(str(source / ".git"))
    fs.create_file(str(source / ".git" / "config"), contents="[core]")

    archive_name = "docs.tar.gz"
    message = tar.run([source.name, archive_name], shell)

    archive_path = shell.cwd / archive_name
    assert archive_path.exists()
    assert message == f"Created archive '{archive_path}'"

    with tarfile.open(archive_path, "r:gz") as tf:
        names = tf.getnames()

    assert f"{source.name}/readme.txt" in names
    assert all(".git" not in name for name in names)


def test_tar_requires_existing_directory(shell):
    with pytest.raises(CommandError):
        tar.run(["missing", "output.tar.gz"], shell)


def test_tar_rejects_non_directory(fs, shell):
    file_path = shell.cwd / "data.txt"
    fs.create_file(str(file_path), contents="value")

    with pytest.raises(CommandError):
        tar.run([file_path.name, "data.tar.gz"], shell)
