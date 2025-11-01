from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem


class ShellStub:
    """Минимальная заглушка оболочки для команд."""

    def __init__(self, cwd: Path, trash_dir: Path) -> None:
        self.cwd = cwd
        self.trash_dir = trash_dir
        self.undo_stack: list[dict[str, object]] = []
        self.history_entries: list[str] = []

    def push_undo(self, action: dict[str, object]) -> None:
        self.undo_stack.append(action)

    def pop_undo(self) -> dict[str, object] | None:
        if not self.undo_stack:
            return None
        return self.undo_stack.pop()

    def read_history(self, limit: int | None = None) -> list[str]:
        if limit is None:
            return list(self.history_entries)
        return list(self.history_entries[-limit:])


@pytest.fixture
def shell(fs: FakeFilesystem) -> ShellStub:
    home = Path("/home/tester")
    workspace = home / "workspace"
    trash_dir = home / "trash"

    fs.create_dir(str(workspace))
    fs.create_dir(str(trash_dir))

    return ShellStub(cwd=workspace, trash_dir=trash_dir)
