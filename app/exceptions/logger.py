"""
Structured logging configuration for OrgFlow Agent
"""

import logging
import json
from datetime import datetime
from typing import Any, Optional

from app.config.settings import settings


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields from the record in a generic way.
        builtin_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }

        for key, value in record.__dict__.items():
            if key in builtin_fields or key.startswith("_"):
                continue
            log_obj[key] = value

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_obj, default=str)


def setup_logging(
    log_level: str = "INFO",
    use_json: bool = True,
) -> None:
    """
    Configure logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting
    """

    # Get log level from settings or use default
    env_log_level = (settings.LOG_LEVEL or log_level).upper()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, env_log_level))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(
        getattr(logging, env_log_level)
    )

    # Set formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] "
            "[%(name)s:%(funcName)s:%(lineno)d] "
            "%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Set up specific loggers
    logging.getLogger("sqlalchemy").setLevel(
        logging.WARNING
    )
    logging.getLogger("urllib3").setLevel(
        logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
