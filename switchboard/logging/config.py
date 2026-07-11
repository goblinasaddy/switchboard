import logging
from typing import Any
import structlog

def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure system-wide structured logging using structlog and Rich.
    
    Args:
        log_level: The minimum level name to record (DEBUG, INFO, WARNING, ERROR).
    """
    # Map input string level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard logging to route through RichHandler
    from rich.logging import RichHandler
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=True, markup=True)],
        force=True,  # Override any default logger configurations
    )

    # Configure structlog to use stdlib compatibility
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # For local dev console, format as a dictionary key-value or pretty string
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    Get a pre-configured structured logger instance.
    
    Args:
        name: Name of the subsystem calling get_logger.
    """
    return structlog.get_logger(name)
