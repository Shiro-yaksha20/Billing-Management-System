"""Logging utilities."""

from __future__ import annotations

import logging
import os
import sys

from ..constants import LOGS_DIR


def setup_logger() -> logging.Logger:
    """Set up the application logger."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(LOGS_DIR, "app.log")),
            logging.StreamHandler(),
        ],
    )

    return logging.getLogger(__name__)


logger = setup_logger()


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
