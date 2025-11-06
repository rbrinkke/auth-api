import logging
import logging.config
import sys
from pathlib import Path

import structlog
from structlog.typing import EventDict, Processor

LOGS_DIR = Path("/app/logs")
LOGS_DIR.mkdir(exist_ok=True, parents=True)


def add_correlation_id(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    if not event_dict.get("correlation_id"):
        event_dict["correlation_id"] = "-"

    return event_dict


def add_service_info(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "auth-api"
    event_dict["environment"] = "production"

    return event_dict


def json_filter(logger: logging.Logger, name: str, event_dict: EventDict) -> EventDict:
    if "timestamp" not in event_dict:
        import time
        event_dict["timestamp"] = time.time()

    if "level" not in event_dict:
        event_dict["level"] = method_name.upper()

    return event_dict


def setup_logging() -> None:
    structlog.configure(
        processors=[
            add_correlation_id,
            add_service_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addHandler(logging.StreamHandler(sys.stdout))
    uvicorn_access_logger.setLevel(logging.INFO)

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addHandler(logging.StreamHandler(sys.stdout))
    uvicorn_error_logger.setLevel(logging.INFO)

    slowapi_logger = logging.getLogger("slowapi")
    slowapi_logger.addHandler(logging.StreamHandler(sys.stdout))
    slowapi_logger.setLevel(logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


setup_logging()
