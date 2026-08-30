"""
Logging configuration for the FastAPI layer.

One dictConfig call, invoked from main.py before the app does anything
else, replacing the previous bare `logging.basicConfig(level=logging.INFO)`
-- which had no explicit formatter, so log lines carried no timestamp and
nothing distinguishing this app's own records from Uvicorn's/SQLAlchemy's
in a shared stdout stream.

Plain-text formatting, not JSON: python-json-logger isn't a dependency
here (dropped in the dependency-cleanup branch as unused -- see
requirements.txt), and structured JSON logging isn't earning its keep yet
at this project's log volume/scale. A consistent plain format (timestamp,
level, logger name, message) is enough to read/grep locally and in a
container's stdout; revisit if this API ever ships to a real log
aggregator that specifically wants JSON lines.
"""

import logging.config

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configures the root logger -- and hence every module logger under it,
    including "api" (app-lifecycle events, e.g. the startup DB check) and
    "api.request" (per-request access log, see main.py) -- with one
    consistent Formatter/StreamHandler pair.

    `disable_existing_loggers: False` is deliberate: dictConfig defaults
    to tearing down every logger that already exists (e.g. ones Uvicorn or
    SQLAlchemy configured on import, before this function ever runs),
    which would silently mute them. Leaving them alone means they inherit
    this same root handler/formatter instead of losing their own output.
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": LOG_FORMAT},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": level,
            },
        }
    )
