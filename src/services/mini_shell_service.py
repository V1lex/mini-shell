from __future__ import annotations

import os
from os import PathLike
from pathlib import Path
from typing import Any

from src.commands import (
    cat as cat_command,
    cd as cd_command,
    cp as cp_command,
    grep as grep_command,
    history as history_command,
    ls as ls_command,
    mv as mv_command,
    pwd as pwd_command,
    rm as rm_command,
    tar as tar_command,
    undo as undo_command,
    untar as untar_command,
    unzip as unzip_command,
    zip as zip_command,
)
from src.commands.utils import CommandError, resolve_path
from src.enums.file_mode import FileReadMode
from src.services.base import OSConsoleServiceBase
from src.shell import Shell


class MiniShellService(OSConsoleServiceBase):
    """Адаптер Shell к интерфейсу, похожему на пример преподавателя."""

    def __init__(self, shell: Shell) -> None:
        super().__init__(shell.logger)
        self._shell = shell

    def _to_argument(self, value: PathLike[str] | str) -> str:
        return os.fspath(value)

    def _invoke_command(self, command_name: str, module, args: list[str]) -> str:
        try:
            return module.run(args, self._shell)
        except CommandError as error:
            self._raise_for_command(command_name, str(error))
            raise  # недостижимо

    def _raise_for_command(self, command_name: str, message: str) -> None:
        lowered = message.lower()
        if "no such file or directory" in lowered or "not found" in lowered:
            raise FileNotFoundError(message)
        if "must be a directory" in lowered or "not a directory" in lowered:
            raise NotADirectoryError(message)
        if (
            "is a directory" in lowered
            or "required to copy directories" in lowered
            or "must be a file" in lowered
        ):
            raise IsADirectoryError(message)
        if "source and destination are the same" in lowered:
            raise ValueError(message)
        if "unsupported option" in lowered or "missing operand" in lowered or "usage:" in lowered:
            raise ValueError(message)
        if "argument must" in lowered or "must be positive" in lowered or "invalid pattern" in lowered:
            raise ValueError(message)
        if "refusing to remove" in lowered:
            raise PermissionError(message)
        if "unsafe" in lowered:
            raise ValueError(message)
        if "unexpected failure" in lowered or "failed to" in lowered or "error" in lowered:
            raise OSError(message)
        raise RuntimeError(f"{command_name}: {message}")

    def _resolve(self, path: PathLike[str] | str) -> Path:
        return resolve_path(self._to_argument(path), self._shell.cwd)

    @property
    def cwd(self) -> Path:
        return self._shell.cwd

    @property
    def undo_stack(self) -> list[dict[str, Any]]:
        return self._shell.undo_stack

    @property
    def trash_dir(self) -> Path:
        return self._shell.trash_dir

    @property
    def history_file(self) -> Path:
        return self._shell.history_file

    def ls(self, path: PathLike[str] | str | None = None, *, long: bool = False) -> list[str]:
        args: list[str] = []
        if long:
            args.append("-l")
        if path is not None:
            args.append(self._to_argument(path))

        output = self._invoke_command("ls", ls_command, args)
        if not output:
            return []
        return [f"{line}\n" for line in output.splitlines()]

    def cat(
        self,
        filename: PathLike[str] | str,
        *,
        mode: FileReadMode = FileReadMode.string,
    ) -> str | bytes:
        path = self._resolve(filename)
        if mode == FileReadMode.bytes:
            if not path.exists():
                raise FileNotFoundError(filename)
            if path.is_dir():
                raise IsADirectoryError(filename)
            return path.read_bytes()

        return self._invoke_command("cat", cat_command, [self._to_argument(filename)])

    def cd(self, path: PathLike[str] | str | None = None) -> None:
        args: list[str] = []
        if path is not None:
            args.append(self._to_argument(path))
        self._invoke_command("cd", cd_command, args)

    def pwd(self) -> str:
        return self._invoke_command("pwd", pwd_command, [])

    def cp(self, source: PathLike[str] | str, destination: PathLike[str] | str, *, recursive: bool = False) -> str:
        args: list[str] = []
        if recursive:
            args.append("-r")
        args.extend([self._to_argument(source), self._to_argument(destination)])
        return self._invoke_command("cp", cp_command, args)

    def mv(self, source: PathLike[str] | str, destination: PathLike[str] | str) -> str:
        args = [self._to_argument(source), self._to_argument(destination)]
        return self._invoke_command("mv", mv_command, args)

    def rm(self, path: PathLike[str] | str, *, recursive: bool = False) -> str:
        args: list[str] = []
        if recursive:
            args.append("-r")
        args.append(self._to_argument(path))
        return self._invoke_command("rm", rm_command, args)

    def zip(self, source: PathLike[str] | str, archive: PathLike[str] | str) -> str:
        args = [self._to_argument(source), self._to_argument(archive)]
        return self._invoke_command("zip", zip_command, args)

    def unzip(self, archive: PathLike[str] | str) -> str:
        return self._invoke_command("unzip", unzip_command, [self._to_argument(archive)])

    def tar(self, source: PathLike[str] | str, archive: PathLike[str] | str) -> str:
        args = [self._to_argument(source), self._to_argument(archive)]
        return self._invoke_command("tar", tar_command, args)

    def untar(self, archive: PathLike[str] | str) -> str:
        return self._invoke_command("untar", untar_command, [self._to_argument(archive)])

    def grep(
        self,
        pattern: str,
        path: PathLike[str] | str | None = None,
        *,
        recursive: bool = False,
        ignore_case: bool = False,
    ) -> str:
        args: list[str] = []
        if recursive:
            args.append("-r")
        if ignore_case:
            args.append("-i")
        args.append(pattern)
        if path is not None:
            args.append(self._to_argument(path))
        return self._invoke_command("grep", grep_command, args)

    def history(self, limit: int | None = None) -> list[str]:
        args: list[str] = []
        if limit is not None:
            args.append(str(limit))
        output = self._invoke_command("history", history_command, args)
        if output == "History is empty":
            return []
        return output.splitlines()

    def undo(self) -> str:
        return self._invoke_command("undo", undo_command, [])

    def record_history(self, command_line: str) -> None:
        self._shell.record_history(command_line)

    def read_history(self, limit: int | None = None) -> list[str]:
        return self._shell.read_history(limit)

    def push_undo(self, action: dict[str, Any]) -> None:
        self._shell.push_undo(action)

    def pop_undo(self) -> dict[str, Any] | None:
        return self._shell.pop_undo()
