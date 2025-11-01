import zipfile

import pytest

from src.commands import zip
from src.commands.utils import CommandError


def test_zip_creates_archive_without_git(fs, shell):
    source = shell.cwd / "project"
    fs.create_dir(str(source))
    fs.create_file(str(source / "app.py"), contents="print('ok')")
    fs.create_dir(str(source / ".git"))
    fs.create_file(str(source / ".git" / "config"), contents="secret")

    archive_name = "project.zip"
    message = zip.run([source.name, archive_name], shell)

    archive_path = shell.cwd / archive_name
    assert archive_path.exists()
    assert message == f"Created archive '{archive_path}'"

    with zipfile.ZipFile(archive_path, "r") as zf:
        names = zf.namelist()

    assert "project/app.py" in names
    assert all(".git" not in name for name in names)


def test_zip_requires_existing_directory(shell):
    with pytest.raises(CommandError):
        zip.run(["missing", "output.zip"], shell)


def test_zip_rejects_non_directory(fs, shell):
    file_path = shell.cwd / "file.txt"
    fs.create_file(str(file_path), contents="data")

    with pytest.raises(CommandError):
        zip.run([file_path.name, "file.zip"], shell)
