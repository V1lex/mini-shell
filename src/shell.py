import shlex
from pathlib import Path

import typer

from src import config
from src.commands import (
    cat,
    cd,
    cp,
    grep,
    history,
    ls,
    mv,
    pwd,
    rm,
    tar,
    undo,
    untar,
    unzip,
    zip,
)
from src.commands.utils import CommandError
from src.logger_config import setup_logger


class Shell:
    """Мини-оболочка со встроенными командами."""

    def __init__(self) -> None:
        """Инициализирует состояние оболочки и регистрирует команды."""
        self.cwd = Path.home()
        self.logger = setup_logger()
        self.commands: dict[str, object] = {}
        self.history_file = Path(config.HISTORY_FILE)
        self.history_file.touch(exist_ok=True)
        self.trash_dir = Path(config.TRASH_DIR)
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        self.undo_stack: list[dict[str, str]] = []

        self._register_builtin_commands()
        self._register_internal_commands()

    def register_command(self, name: str, handler) -> None:
        """Регистрирует функцию-обработчик под указанным именем команды."""
        self.commands[name] = handler

    def _register_builtin_commands(self) -> None:
        """Подготавливает базовый набор команд файловой системы."""
        mapping = {
            "cd": cd,
            "ls": ls,
            "cat": cat,
            "cp": cp,
            "mv": mv,
            "rm": rm,
            "pwd": pwd,
            "history": history,
            "undo": undo,
            "zip": zip,
            "unzip": unzip,
            "tar": tar,
            "untar": untar,
            "grep": grep,
        }

        for name, module in mapping.items():
            handler = getattr(module, "run", None)
            if handler:
                self.register_command(name, handler)

    def _register_internal_commands(self) -> None:
        """Добавляет служебные команды оболочки."""
        self.register_command("help", self.help_command)
        self.register_command("exit", self.exit_command)

    def record_history(self, command_line: str) -> None:
        """Сохраняет введённую строку команды в файл истории."""
        with self.history_file.open("a", encoding="utf-8") as file:
            file.write(command_line + "\n")

    def read_history(self, limit: int | None = None) -> list[str]:
        """Возвращает команды истории, при необходимости оставляя хвост."""
        lines = self.history_file.read_text(encoding="utf-8").splitlines()
        if limit is None:
            return lines
        return lines[-limit:]

    def push_undo(self, action: dict[str, str]) -> None:
        """Добавляет обратимое действие в стек undo."""
        self.undo_stack.append(action)

    def pop_undo(self) -> dict[str, str] | None:
        """Извлекает последнее обратимое действие."""
        if not self.undo_stack:
            return None
        return self.undo_stack.pop()

    def run(self) -> None:
        """Запускает REPL-цикл до выхода пользователя."""
        self._show_banner()
        while True:
            try:
                command_line = self._read_command()
                if command_line == "":
                    continue
                self.record_history(command_line)
                self._handle_command(command_line)
            except (EOFError, KeyboardInterrupt):
                self._echo_warning("\nExiting shell.")
                self.logger.info("Shell exited by user")
                break

    repl = run

    def _handle_command(self, command_line: str) -> None:
        """Обрабатывает введённую команду с логированием результата."""
        self.logger.info(command_line)
        try:
            result = self.execute(command_line)
            if result:
                self._echo_success(result)
        except CommandError as error:
            message = str(error)
            self._echo_error(message)
            self.logger.error(f"ERROR: {message}")
        except SystemExit as exit_error:
            raise exit_error
        except Exception as error:
            message = f"Unexpected error: {error}"
            self._echo_error(message)
            self.logger.error(f"ERROR: {message}")

    def execute(self, command_line: str) -> str | None:
        """Разбирает строку и запускает соответствующую команду."""
        parts = shlex.split(command_line)
        if not parts:
            return None
        command, *args = parts
        handler = self.commands.get(command)
        if handler is None or not callable(handler):
            raise CommandError(f"{command}: command not found")
        return handler(args, self)

    def _read_command(self) -> str:
        """Отображает приглашение и возвращает введённую строку."""
        prompt_label = self._format_prompt()
        prompt_marker = typer.style(
            " $ ", fg=typer.colors.BRIGHT_WHITE, bold=True)
        typer.secho(prompt_label + prompt_marker, nl=False)
        return input().strip()

    def _format_prompt(self) -> str:
        """Формирует короткое имя директории для приглашения."""
        home = Path.home()
        if self.cwd == home:
            label = "~"
        else:
            label = self.cwd.name or "/"
        return typer.style(label, fg=typer.colors.BRIGHT_CYAN, bold=True)

    def _show_banner(self) -> None:
        """Печатает приветственным баннер."""
        title = " MINI SHELL "
        border = "+" + "-" * len(title) + "+"
        columns = typer.get_terminal_size()[0]
        width = max(columns, len(border))
        typer.secho(border.center(width),
                    fg=typer.colors.BRIGHT_MAGENTA, bold=True)
        typer.secho(title.center(width),
                    fg=typer.colors.BRIGHT_MAGENTA, bold=True)
        typer.secho(border.center(width),
                    fg=typer.colors.BRIGHT_MAGENTA, bold=True)
        message = (
            "Type 'help' for the command list. Use 'exit' or Ctrl-D to quit."
        )
        typer.secho(message.center(width), fg=typer.colors.BRIGHT_WHITE)

    def _echo_success(self, message: str) -> None:
        """Выводит результат команды зелёным цветом."""
        typer.secho(message, fg=typer.colors.BRIGHT_GREEN)

    def _echo_error(self, message: str) -> None:
        """Печатает сообщение об ошибке в рамке."""
        typer.secho(self._boxed_text(message), fg=typer.colors.BRIGHT_RED)

    def _echo_warning(self, message: str) -> None:
        """Выводит предупреждение жёлтым цветом."""
        typer.secho(message, fg=typer.colors.YELLOW)

    def _boxed_text(self, message: str) -> str:
        """Окружает текст рамкой для акцентирования."""
        lines = message.splitlines() or [""]
        width = max(len(line) for line in lines)
        top = "+" + "-" * (width + 2) + "+"
        bottom = top
        body = "\n".join(f"| {line.ljust(width)} |" for line in lines)
        return "\n".join([top, body, bottom])

    def help_command(self, _args: list[str], _shell: "Shell") -> str:
        """Возвращает перечисление доступных команд."""
        names = ", ".join(sorted(self.commands))
        return f"Available commands: {names}"

    def exit_command(self, _args: list[str], _shell: "Shell") -> None:
        """Завершает работу оболочки."""
        self.logger.info("Shell terminated via exit command")
        raise SystemExit
