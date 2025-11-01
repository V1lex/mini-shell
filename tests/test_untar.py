import io
import tarfile
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from src.commands import untar
from src.commands.utils import CommandError


def _write_tar(archive: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(str(archive), "w:gz") as tf:
        for name, content in members.items():
            data = content if isinstance(content, bytes) else content.encode("utf-8")
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            if name.endswith("/"):
                info.type = tarfile.DIRTYPE
                tf.addfile(info)
            else:
                tf.addfile(info, io.BytesIO(data))


def test_untar_extracts_archive(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    archive = home_dir / "bundle.tar.gz"
    _write_tar(
        archive,
        {
            "bundle/readme.txt": "hello",
            "bundle/src/main.py": "print('ok')",
        },
    )

    message = untar.run(["bundle.tar.gz"], shell_instance)

    bundle_dir = home_dir / "bundle"
    assert bundle_dir.is_dir()
    assert (bundle_dir / "readme.txt").read_text() == "hello"
    assert (bundle_dir / "src" / "main.py").read_text() == "print('ok')"
    assert "Unpacked" in message


def test_untar_skips_git_entries(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    archive = home_dir / "repo.tar.gz"
    _write_tar(
        archive,
        {
            "repo/.git/config": "[core]",
            "repo/file.txt": "data",
        },
    )

    untar.run(["repo.tar.gz"], shell_instance)

    repo_dir = home_dir / "repo"
    assert repo_dir.exists()
    assert (repo_dir / "file.txt").read_text() == "data"
    assert not (repo_dir / ".git").exists()


def test_untar_rejects_unsafe_path(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    archive = home_dir / "unsafe.tar.gz"
    _write_tar(archive, {"../evil.txt": "oops"})

    with pytest.raises(CommandError):
        untar.run(["unsafe.tar.gz"], shell_instance)

    assert not (home_dir.parent / "evil.txt").exists()


def test_untar_creates_unique_root_when_conflicts(
    fs: FakeFilesystem,
    shell_instance,
    home_dir,
) -> None:
    fs.create_dir(str(home_dir / "project"))
    archive = home_dir / "project.tar.gz"
    _write_tar(
        archive,
        {
            "project/info.txt": "data",
        },
    )

    message = untar.run(["project.tar.gz"], shell_instance)

    new_dir = home_dir / "project-1"
    assert new_dir.exists()
    assert (new_dir / "info.txt").read_text() == "data"
    assert str(new_dir) in message
