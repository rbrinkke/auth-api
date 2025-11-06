import logging
import logging.config
import os
import sys
from pathlib import Path

import structlog
from structlog.typing import EventDict, Processor

LOGS_DIR = Path("/app/logs")
LOGS_DIR.mkdir(exist_ok=True, parents=True)


def get_log_level() -> int:
    level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return log_level_map.get(level_str, logging.INFO)


def add_correlation_id(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    from app.middleware.correlation import correlation_id_var

    correlation_id = correlation_id_var.get()
    event_dict["correlation_id"] = correlation_id if correlation_id else "-"

    return event_dict


def add_service_info(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "auth-api"
    event_dict["environment"] = os.getenv("ENVIRONMENT", "production")

    return event_dict


def json_filter(logger: logging.Logger, name: str, event_dict: EventDict) -> EventDict:
    if "timestamp" not in event_dict:
        import time
        event_dict["timestamp"] = time.time()

    if "level" not in event_dict:
        event_dict["level"] = method_name.upper()

    return event_dict


def setup_logging() -> None:
    log_level = get_log_level()

    structlog.configure(
        processors=[
            add_correlation_id,
            add_service_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addHandler(logging.StreamHandler(sys.stdout))
    uvicorn_access_logger.setLevel(log_level)

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addHandler(logging.StreamHandler(sys.stdout))
    uvicorn_error_logger.setLevel(log_level)

    slowapi_logger = logging.getLogger("slowapi")
    slowapi_logger.addHandler(logging.StreamHandler(sys.stdout))
    slowapi_logger.setLevel(log_level)


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


setup_logging()
