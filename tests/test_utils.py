from pathlib import Path

from src.commands.utils import resolve_path


def test_resolve_path_handles_home(monkeypatch):
    fake_home = Path("/tmp/homeuser")
    monkeypatch.setenv("HOME", str(fake_home))

    result = resolve_path("~/documents", Path("/workspace"))

    assert result == (fake_home / "documents").resolve()


def test_resolve_path_returns_absolute_for_relative():
    cwd = Path("/workspace")
    result = resolve_path("notes/file.txt", cwd)

    assert result == (cwd / "notes/file.txt").resolve()


def test_resolve_path_preserves_absolute_path():
    cwd = Path("/workspace")
    absolute = Path("/data/output.txt")

    assert resolve_path(str(absolute), cwd) == absolute.resolve()
