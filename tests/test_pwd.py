from src.commands import pwd


def test_pwd_returns_working_directory(shell):
    result = pwd.run([], shell)
    assert result == str(shell.cwd)


def test_pwd_ignores_extra_arguments(shell):
    result = pwd.run(["unexpected"], shell)
    assert result == str(shell.cwd)
