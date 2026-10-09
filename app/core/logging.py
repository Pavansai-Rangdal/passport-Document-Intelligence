"""Structured logging configuration."""

import logging
import sys

import structlog
from structlog.types import EventDict, Processor

from app.core.config import get_settings


def add_app_context(_: str, __: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["environment"] = settings.environment
    event_dict["version"] = settings.app_version
    return event_dict


def drop_color_message_key(_: str, __: str, event_dict: EventDict) -> EventDict:
    """Remove color message key for non-TTY output."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """Configure structured logging."""
    settings = get_settings()

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
    ]

    if settings.log_format == "json":
        processors.extend([
            structlog.processors.JSONRenderer(),
        ])
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ])

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(settings.log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging for compatibility
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, settings.log_level),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
