def run(args: list[str], shell) -> str:
    """Возвращает текущий рабочий каталог оболочки."""
    return str(shell.cwd)
