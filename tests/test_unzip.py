import zipfile
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.commands import unzip
from src.commands.utils import CommandError


def _create_zip(path: Path, files: dict[str, bytes | str]) -> None:
    with zipfile.ZipFile(str(path), "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)


def test_unzip_extracts_archive(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    archive = home_dir / "project.zip"
    _create_zip(
        archive,
        {
            "project/readme.txt": "hello",
            "project/src/main.py": "print('ok')",
        },
    )

    message = unzip.run(["project.zip"], shell_instance)

    target_dir = home_dir / "project"
    assert target_dir.is_dir()
    assert (target_dir / "readme.txt").read_text() == "hello"
    assert (target_dir / "src" / "main.py").read_text() == "print('ok')"
    assert "Unpacked" in message


def test_unzip_skips_git_entries(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    archive = home_dir / "repo.zip"
    _create_zip(
        archive,
        {
            "repo/.git/config": "[core]",
            "repo/file.txt": "data",
        },
    )

    unzip.run(["repo.zip"], shell_instance)

    repo_dir = home_dir / "repo"
    assert repo_dir.exists()
    assert (repo_dir / "file.txt").read_text() == "data"
    assert not (repo_dir / ".git").exists()


def test_unzip_rejects_unsafe_path(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    archive = home_dir / "unsafe.zip"
    _create_zip(archive, {"../evil.txt": "oops"})

    with pytest.raises(CommandError):
        unzip.run(["unsafe.zip"], shell_instance)

    assert not (home_dir.parent / "evil.txt").exists()


def test_unzip_creates_unique_root_when_conflicts(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    fs.create_dir(str(home_dir / "project"))
    archive = home_dir / "project.zip"
    _create_zip(
        archive,
        {
            "project/info.txt": "data",
        },
    )

    message = unzip.run(["project.zip"], shell_instance)

    new_dir = home_dir / "project-1"
    assert new_dir.exists()
    assert (new_dir / "info.txt").read_text() == "data"
    assert str(new_dir) in message
