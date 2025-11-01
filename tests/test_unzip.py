import zipfile
from pathlib import Path

import pytest

from src.commands import unzip
from src.commands.utils import CommandError


def _build_zip_with_project(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("project/readme.txt", "doc")
        zf.writestr("project/.git/config", "secret")


def test_unzip_extracts_archive(fs, shell):
    zip_path = shell.cwd / "project.zip"
    _build_zip_with_project(zip_path)

    message = unzip.run([zip_path.name], shell)

    extracted = shell.cwd / "project"
    assert extracted.exists()
    assert (extracted / "readme.txt").read_text(encoding="utf-8") == "doc"
    assert not (extracted / ".git").exists()
    assert message == f"Unpacked '{zip_path}' to '{extracted}'"


def test_unzip_creates_unique_directory_when_target_exists(fs, shell):
    zip_path = shell.cwd / "dataset.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("dataset/info.txt", "data")

    existing = shell.cwd / "dataset"
    fs.create_dir(str(existing))

    result = unzip.run([zip_path.name], shell)

    expected_dir = shell.cwd / "dataset-1"
    assert expected_dir.exists()
    assert (expected_dir / "info.txt").read_text(encoding="utf-8") == "data"
    assert result == f"Unpacked '{zip_path}' to '{expected_dir}'"


def test_unzip_rejects_unsafe_members(fs, shell):
    zip_path = shell.cwd / "bad.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../evil.txt", "danger")

    with pytest.raises(CommandError):
        unzip.run([zip_path.name], shell)
