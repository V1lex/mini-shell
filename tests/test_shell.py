import logging
from pathlib import Path

import pytest

from src import config
from src.commands.utils import CommandError
from src.shell import Shell


@pytest.fixture
def configured_shell(fs, monkeypatch):
    base_dir = Path("/app")
    fs.create_dir(str(base_dir))
    monkeypatch.setattr(config, "BASE_DIR", base_dir)
    monkeypatch.setattr(config, "LOG_FILE", base_dir / "shell.log")
    monkeypatch.setattr(config, "HISTORY_FILE", base_dir / "history.log")
    monkeypatch.setattr(config, "TRASH_DIR", base_dir / ".trash")

    home_path = Path.home()
    if str(home_path) != "/":
        fs.create_dir(str(home_path.parent))
    fs.create_dir(str(home_path))

    logger = logging.getLogger("shell")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    shell = Shell()
    shell._expected_home = home_path
    return shell


def test_shell_execute_unknown_command(configured_shell):
    with pytest.raises(CommandError):
        configured_shell.execute("unknown")


def test_shell_execute_dispatches_to_registered_command(configured_shell):
    captured = {}

    def handler(args: list[str], shell) -> str:
        captured["args"] = args
        captured["cwd"] = shell.cwd
        return "ok"

    configured_shell.register_command("echo", handler)

    result = configured_shell.execute("echo hello world")

    assert result == "ok"
    assert captured["args"] == ["hello", "world"]
    assert captured["cwd"] == configured_shell._expected_home


def test_shell_records_history_lines(configured_shell):
    configured_shell.record_history("first")
    configured_shell.record_history("second")

    history_content = configured_shell.history_file.read_text(encoding="utf-8")

    assert history_content.splitlines() == ["first", "second"]


def test_shell_read_history_limit(configured_shell):
    configured_shell.record_history("cmd1")
    configured_shell.record_history("cmd2")
    configured_shell.record_history("cmd3")

    assert configured_shell.read_history(limit=2) == ["cmd2", "cmd3"]


def test_shell_executes_builtin_command(configured_shell, fs):
    temp_dir = Path("/workspace/run")
    fs.create_dir(str(temp_dir))
    configured_shell.cwd = temp_dir

    result = configured_shell.execute("pwd")

    assert result == str(temp_dir)


def test_shell_logs_successful_command(configured_shell, monkeypatch):
    monkeypatch.setattr(configured_shell, "_echo_success", lambda message: None)

    configured_shell._handle_command("pwd")

    for handler in configured_shell.logger.handlers:
        handler.flush()

    log_content = Path(config.LOG_FILE).read_text(encoding="utf-8")
    assert "pwd" in log_content


def test_shell_logs_error_on_unknown_command(configured_shell, monkeypatch):
    monkeypatch.setattr(configured_shell, "_echo_error", lambda message: None)

    configured_shell._handle_command("unknown_command")

    for handler in configured_shell.logger.handlers:
        handler.flush()

    log_content = Path(config.LOG_FILE).read_text(encoding="utf-8")
    assert "unknown_command" in log_content
    assert "ERROR:" in log_content
