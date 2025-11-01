from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "shell.log"
HISTORY_FILE = BASE_DIR / "history.log"
TRASH_DIR = BASE_DIR / ".trash"

LOG_LEVEL = "INFO"
