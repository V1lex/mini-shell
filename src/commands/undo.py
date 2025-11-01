import logging
import shutil
from pathlib import Path

from .utils import CommandError

logger = logging.getLogger("shell")


def run(args: list[str], shell) -> str:
    """Отменяет последнее действие из поддерживаемого списка (cp/mv/rm)."""
    if args:
        raise CommandError("undo: this command does not accept arguments")

    action = shell.pop_undo()
    if action is None:
        raise CommandError("undo: no actions to undo")

    try:
        kind = action.get("command")
        if kind == "cp":
            return _undo_copy(action)
        if kind == "mv":
            return _undo_move(action)
        if kind == "rm":
            return _undo_remove(action)
        raise CommandError(f"undo: unsupported action '{kind}'")
    except CommandError as error:
        shell.push_undo(action)
        raise error
    except Exception as error:
        shell.push_undo(action)
        raise CommandError(f"undo: unexpected failure: {error}") from error


def _undo_copy(action: dict[str, str]) -> str:
    """Удаляет файл или каталог, созданный командой cp."""
    target = Path(action["target"])
    if not target.exists():
        raise CommandError(f"undo: copied target '{target}' no longer exists")
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    logger.debug(f"undo copy removed {target}")
    return f"Undo: removed '{target}'"


def _undo_move(action: dict[str, str]) -> str:
    """Возвращает файл или каталог на исходное место после mv."""
    source = Path(action["source"])
    destination = Path(action["destination"])
    if not destination.exists():
        raise CommandError(f"undo: moved target '{destination}' not found")
    source.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(destination), str(source))
    logger.debug(f"undo move restored {source} from {destination}")
    return f"Undo: moved back to '{source}'"


def _undo_remove(action: dict[str, str]) -> str:
    """Восстанавливает файл или каталог из корзины после rm."""
    original = Path(action["original"])
    trash_path = Path(action["trash"])
    if not trash_path.exists():
        raise CommandError(f"undo: trash entry '{trash_path}' missing")
    original.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(trash_path), str(original))
    logger.debug(f"undo remove restored {original} from {trash_path}")
    return f"Undo: restored '{original}'"
