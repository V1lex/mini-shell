import pytest

from src.commands import grep
from src.commands.utils import CommandError


def test_grep_returns_matching_lines_from_file(fs, shell):
    file_path = shell.cwd / "notes.txt"
    fs.create_file(
        str(file_path),
        contents="first line\nsecond line has keyword\nlast line",
    )

    result = grep.run(["keyword", file_path.name], shell)

    assert result == "notes.txt 2:second line has keyword"


def test_grep_searches_recursively(fs, shell):
    docs = shell.cwd / "docs"
    fs.create_dir(str(docs))
    nested = docs / "guide.txt"
    fs.create_file(str(nested), contents="read the manual")

    outcome = grep.run(["-r", "manual", docs.name], shell)

    assert outcome == "docs/guide.txt 1:read the manual"


def test_grep_honors_case_insensitive_flag(fs, shell):
    file_path = shell.cwd / "story.txt"
    fs.create_file(str(file_path), contents="Adventure Time")

    response = grep.run(["-i", "adventure", file_path.name], shell)

    assert response == "story.txt 1:Adventure Time"


def test_grep_reports_absence_of_matches(fs, shell):
    file_path = shell.cwd / "report.txt"
    fs.create_file(str(file_path), contents="all clear")

    message = grep.run(["alert", file_path.name], shell)

    assert message == "no matches found"


def test_grep_fails_for_missing_path(shell):
    with pytest.raises(CommandError):
        grep.run(["pattern", "unknown.txt"], shell)


def test_grep_requires_recursive_flag_for_directory(fs, shell):
    directory = shell.cwd / "folder"
    fs.create_dir(str(directory))

    with pytest.raises(CommandError):
        grep.run(["pattern", directory.name], shell)


def test_grep_requires_arguments(shell):
    with pytest.raises(CommandError):
        grep.run([], shell)


def test_grep_rejects_unknown_option(shell):
    with pytest.raises(CommandError):
        grep.run(["-x", "pattern"], shell)


def test_grep_validates_regex(fs, shell):
    file_path = shell.cwd / "data.txt"
    fs.create_file(str(file_path), contents="content")

    with pytest.raises(CommandError):
        grep.run(["[", file_path.name], shell)


def test_grep_recursive_without_path_uses_cwd(fs, shell):
    file_path = shell.cwd / "log.txt"
    fs.create_file(str(file_path), contents="error occurred")

    result = grep.run(["-r", "error"], shell)

    assert result == "./log.txt 1:error occurred"


def test_grep_combines_recursive_and_ignore_case(fs, shell):
    target_dir = shell.cwd / "src"
    fs.create_dir(str(target_dir))
    fs.create_file(str(target_dir / "a.txt"), contents="First KEYword")
    fs.create_file(str(target_dir / "b.txt"), contents="keyword second")

    output = grep.run(["-ri", "keyword", target_dir.name], shell)
    lines = sorted(output.splitlines())

    assert lines == [
        "src/a.txt 1:First KEYword",
        "src/b.txt 1:keyword second",
    ]
