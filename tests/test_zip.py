import zipfile
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.commands import zip
from src.commands.utils import CommandError


def _zip_entries(archive: Path) -> set[str]:
    with zipfile.ZipFile(archive, "r") as zf:
        return set(zf.namelist())


def test_zip_creates_archive_excluding_git(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    source = home_dir / "src"
    fs.create_dir(str(source))
    fs.create_file(str(source / "main.py"), contents="print('ok')")
    git_dir = source / ".git"
    fs.create_dir(str(git_dir))
    fs.create_file(str(git_dir / "config"), contents="[core]")

    archive = home_dir / "src.zip"
    message = zip.run(["src", "src.zip"], shell_instance)

    assert "Created archive" in message
    assert archive.exists()
    entries = _zip_entries(archive)
    assert "src/main.py" in entries
    assert all(".git" not in name for name in entries)


def test_zip_requires_existing_directory(shell_instance) -> None:
    with pytest.raises(CommandError):
        zip.run(["missing", "archive.zip"], shell_instance)


def test_zip_rejects_non_directory_source(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    fs.create_file(str(home_dir / "file.txt"), contents="data")

    with pytest.raises(CommandError):
        zip.run(["file.txt", "archive.zip"], shell_instance)
