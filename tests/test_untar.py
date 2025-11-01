import tarfile

import pytest

from src.commands import untar
from src.commands.utils import CommandError


def test_untar_extracts_archive(fs, shell):
    source_dir = shell.cwd / "sources" / "package"
    archive_path = shell.cwd / "package.tar.gz"
    fs.create_dir(str(source_dir))
    fs.create_file(str(source_dir / "file.txt"), contents="data")
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(str(source_dir), arcname="package")

    message = untar.run([archive_path.name], shell)

    extracted = shell.cwd / "package"
    assert extracted.exists()
    assert (extracted / "file.txt").read_text(encoding="utf-8") == "data"
    assert message == f"Unpacked '{archive_path}' to '{extracted}'"


def test_untar_creates_unique_directory_when_target_exists(fs, shell):
    source_dir = shell.cwd / "sources" / "dataset"
    archive_path = shell.cwd / "dataset.tar.gz"
    fs.create_dir(str(source_dir))
    fs.create_file(str(source_dir / "file.txt"), contents="data")
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(str(source_dir), arcname="dataset")

    existing = shell.cwd / "dataset"
    fs.create_dir(str(existing))

    result = untar.run([archive_path.name], shell)

    expected_dir = shell.cwd / "dataset-1"
    assert expected_dir.exists()
    assert (expected_dir / "file.txt").read_text(encoding="utf-8") == "data"
    assert result == f"Unpacked '{archive_path}' to '{expected_dir}'"


def test_untar_rejects_unsafe_members(fs, shell):
    archive_path = shell.cwd / "bad.tar.gz"
    temp_dir = shell.cwd / "temp"
    fs.create_dir(str(temp_dir))
    dummy = temp_dir / "payload.txt"
    fs.create_file(str(dummy), contents="danger")
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(str(dummy), arcname="../evil.txt")

    with pytest.raises(CommandError):
        untar.run([archive_path.name], shell)
