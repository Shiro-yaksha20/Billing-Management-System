"""Logging utilities with lazy initialization."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from ..constants import LOGS_DIR

_LOGGER: logging.Logger | None = None
_CONFIGURED = False


def setup_logger() -> logging.Logger:
    """Set up the application logger."""
    global _CONFIGURED

    logger_instance = logging.getLogger("billing_app")
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    if _CONFIGURED:
        return logger_instance

    logger_instance.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger_instance.handlers.clear()
    logger_instance.addHandler(file_handler)
    logger_instance.addHandler(stream_handler)
    logger_instance.propagate = False

    _CONFIGURED = True
    return logger_instance


def get_logger() -> logging.Logger:
    """Return a lazily initialized logger instance."""
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = setup_logger()
    return _LOGGER


class _LazyLogger:
    """Proxy logger that initializes handlers on first use."""

    def __getattr__(self, attr_name: str):
        return getattr(get_logger(), attr_name)


logger = _LazyLogger()


def log_info(message: str) -> None:
    try:
        logger.info(message)
    except Exception as exc:
        print(f"[LOGGER FAILED] INFO: {message} (Error: {exc})", file=sys.stderr)


def log_error(message: str) -> None:
    try:
        logger.error(message)
    except Exception as exc:
        print(f"[LOGGER FAILED] ERROR: {message} (Error: {exc})", file=sys.stderr)
