"""
Structured logging for the Industrial AI Inspection project.

Replaces ad-hoc print() statements with a configurable logger.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.utils.config import get_app_config, clear_cache


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    name: str = "industrial_ai"
) -> logging.Logger:
    """
    Configure and return a logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to app config.
        log_file: Optional path to log file. Defaults to logs/app.log.
        name: Logger name.

    Returns:
        Configured logging.Logger instance.
    """
    # Get level from app config if not provided
    if level is None:
        app_config = get_app_config()
        level = app_config.get("app", {}).get("log_level", "INFO")

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates on re-import
    logger.handlers.clear()

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        app_config = get_app_config()
        logs_dir = Path(app_config.get("paths", {}).get("logs_dir", "logs"))
        log_file = str(logs_dir / "app.log")

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


# Default logger instance
logger = setup_logging()


def get_logger(name: str = "industrial_ai") -> logging.Logger:
    """Get a logger instance (uses existing if already configured)."""
    existing = logging.getLogger(name)
    if existing.handlers:
        return existing
    return setup_logging(name=name)