import logging
import logging.config
import os
import sys
from pathlib import Path

import structlog
import yaml
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


def add_trace_id(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    from app.middleware.correlation import trace_id_var

    trace_id = trace_id_var.get()
    event_dict["trace_id"] = trace_id if trace_id else None

    return event_dict


def add_service_info(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "auth-api"
    event_dict["environment"] = os.getenv("ENVIRONMENT", "production")

    return event_dict


def add_timestamp(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    if "timestamp" not in event_dict:
        from datetime import datetime, timezone
        event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

    if "level" not in event_dict:
        event_dict["level"] = method_name.upper()

    return event_dict


def setup_logging() -> None:
    log_level = get_log_level()

    # Load dictConfig from YAML file
    config_path = Path("/app/config/logging.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        # Fallback to basicConfig if YAML not found
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=log_level,
        )

    # Configure structlog
    structlog.configure(
        processors=[
            add_timestamp,
            add_trace_id,
            add_service_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)


setup_logging()
