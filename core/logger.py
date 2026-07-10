"""
Logger Module.

Configures application-wide logging using Rich console formatting and log rotation
to file.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from rich.logging import RichHandler
from core.config import settings

# Define logs location
LOG_FILE_PATH = settings.BASE_DIR / settings.LOGS_DIR / "pipeline.log"


def setup_logger(name: str = "saas_pipeline") -> logging.Logger:
    """Initialize a logger with Rich handler for console and RotatingFileHandler for log files.

    Args:
        name: Name of the logger instance.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Check if logger is already configured to prevent duplicate handlers
    if logger.handlers:
        return logger
        
    logger.setLevel(settings.LOG_LEVEL.upper())
    logger.propagate = False

    # Console Handler using Rich
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False
    )
    console_handler.setLevel(settings.LOG_LEVEL.upper())
    
    # File Handler with rotation
    file_handler = RotatingFileHandler(
        filename=LOG_FILE_PATH,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Default logger for import convenience
logger = setup_logger()
