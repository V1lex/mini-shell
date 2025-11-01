import logging
from pathlib import Path
from src import config


def setup_logger() -> logging.Logger:
    """Настраивает файловый логгер для оболочки."""
    logger = logging.getLogger("shell")
    if logger.handlers:
        return logger

    log_path = Path(config.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
