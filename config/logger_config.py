import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
import time
import sys
from pathlib import Path


def setup_logger(
    log_dir="logs",
    console_level=logging.WARNING,
    file_level=logging.DEBUG,
    app_name="app",
):
    """Configure and return a logger with multiple handlers.

    Args:
        log_dir: Directory for log files
        console_level: Logging level for console output
        file_level: Logging level for log files
        app_name: Name for the logger

    Returns:
        Configured logger instance
    """
    try:
        Path(log_dir).mkdir(exist_ok=True)
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"Error creating log directory: {e}", file=sys.stderr)
        log_dir = "."

    logger = logging.getLogger(app_name)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        f"{log_dir}/detailed_logs.log",
        mode="a",
        maxBytes=10 * 1024 * 1024,
        backupCount=2,
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    proc_handler = TimedRotatingFileHandler(
        f"{log_dir}/processing.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    proc_handler.setLevel(logging.INFO)
    proc_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    proc_handler.setFormatter(proc_formatter)
    proc_handler.suffix = "%Y-%m-%d"
    logger.addHandler(proc_handler)

    error_handler = RotatingFileHandler(
        f"{log_dir}/errors.log",
        mode="a",
        maxBytes=5 * 1024 * 1024,
        backupCount=1,
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        "%(asctime)s - %(process)d - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)

    logger.info("Logger initialized at %s", time.strftime("%Y-%m-%d %H:%M:%S"))
    return logger


default_logger = setup_logger()

# Export the default_logger as 'logger' for backward compatibility
logger = default_logger

# Example usage:
# from config.logger_config import setup_logger
# logger = setup_logger(app_name="my_module")
# logger.info("Application started")
