"""Logging configuration using structlog."""

import json
import logging
import os
import sys
from typing import Any

import structlog
from structlog.types import EventDict


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log entries.

    This processor adds standard application metadata to every log entry.
    """
    event_dict["app"] = "auth-manager-service"
    return event_dict


def pretty_json(
    logger: structlog.stdlib.BoundLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Prettify JSON values in the event dictionary for better readability in logs.

    Args:
        logger: The logger instance.
        method_name: The name of the logging method.
        event_dict: The event dictionary containing the log data.

    Returns:
        The modified event dictionary with prettified JSON values.
    """
    for key, value in event_dict.items():
        if isinstance(value, dict):
            event_dict[key] = json.dumps(value, indent=2)
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """
        Configure structlog for structured logging with JSON output.

        This function sets up structlog with the following features:
        - JSON output format for production
        - Timestamp in ISO format with UTC timezone
        - Log level filtering
        - Exception formatting with stack traces
        - Request ID correlation (when available)
        - Consistent field naming
        - Context preservation across log calls

        Args:
            log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    t
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors for both structlog and stdlib logging
    shared_processors = [
        # Add context from thread-local storage
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp in ISO format with UTC
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add application context
        add_app_context,
        # Format stack info if present
        structlog.processors.StackInfoRenderer(),
        # Format exceptions with full traceback
        structlog.processors.format_exc_info,
        # Ensure proper unicode handling
        structlog.processors.UnicodeDecoder(),
        structlog.processors.dict_tracebacks,
    ]

    is_dev = os.getenv("ENV", "dev") == "dev"
    renderer = (
        structlog.dev.ConsoleRenderer(
            colors=True,
            sort_keys=True,
        )
        if is_dev
        else structlog.processors.JSONRenderer()
    )

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            # Prepare for stdlib logging
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        # Use stdlib logging as the backend
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache logger instances for performance
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog's formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        # Process logs from non-structlog loggers (e.g., uvicorn, sqlalchemy)
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Set up the root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    # Configure third-party loggers to use appropriate levels
    logging.getLogger("uvicorn").setLevel(numeric_level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structlog logger instance.

    Args:
        name: Optional logger name. If not provided, uses the caller's module name.

    Returns:
        A bound structlog logger instance that supports structured logging

    """
    return structlog.get_logger(name)
