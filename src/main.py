import typer
from src.shell import Shell

app = typer.Typer(help="Mini shell with file management commands")


@app.command()
def run() -> None:
    """Команда CLI для запуска интерактивной оболочки."""
    Shell().run()


def main() -> None:
    """Входная функция, делегирующая управление Typer-приложению."""
    app()


if __name__ == "__main__":
    main()
