"""Utility functions and helpers."""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: Path | None = None) -> None:
    """Configure logging for the application."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    if log_level.upper() != "DEBUG":
        for noisy_logger in ("httpx", "httpcore", "ollama"):
            logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def confirm_prompt(message: str, default: bool = False) -> bool:
    """Ask user for confirmation."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{message} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ("y", "yes")


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to max_length with suffix."""
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix
