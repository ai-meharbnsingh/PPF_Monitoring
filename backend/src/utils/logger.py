"""
Module: logger.py
Purpose:
    Centralised logging setup using loguru.
    All modules call get_logger(__name__) to get a configured logger.
    Log rotation, file output, and level all come from settings.yaml.

Author: PPF Monitoring Team
Created: 2026-02-21
"""

import sys
from pathlib import Path

from loguru import logger as _loguru_logger

from src.config.settings import get_settings

_configured = False


def _configure_logger() -> None:
    """Configure loguru with settings from config. Called once on first use."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    log_file = Path(settings.LOG_FILE_PATH)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    _loguru_logger.remove()

    # Console sink
    _loguru_logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
               "<level>{message}</level>",
        colorize=True,
    )

    # File sink with rotation
    _loguru_logger.add(
        str(log_file),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )

    _configured = True


def get_logger(name: str):
    """
    Return a bound loguru logger for a module.

    Usage:
        logger = get_logger(__name__)
        logger.info("Server started")
        logger.error("Something failed", exc_info=True)
    """
    _configure_logger()
    return _loguru_logger.bind(name=name)
