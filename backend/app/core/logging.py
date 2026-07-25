"""
Structured logging configuration.

Uses stdlib logging with a consistent formatter across the app so that
log lines are greppable and, in production, parseable as structured text.
Call configure_logging() once at process startup (done in main.py).
"""
import logging
import sys

from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Avoid duplicate handlers on reload
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers unless we're actively debugging them
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
