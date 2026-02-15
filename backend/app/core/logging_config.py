import logging
import sys

from pythonjsonlogger import jsonlogger


class ContextFilter(logging.Filter):
    """Injeta trace_id e contexto da requisição nos log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = "no-request-context"
        if not hasattr(record, "method"):
            record.method = ""
        if not hasattr(record, "path"):
            record.path = ""
        if not hasattr(record, "user_id"):
            record.user_id = ""
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON customizado com campos padronizados."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = self.formatTime(record)
        log_record["trace_id"] = getattr(record, "trace_id", "")
        log_record["method"] = getattr(record, "method", "")
        log_record["path"] = getattr(record, "path", "")
        log_record["user_id"] = getattr(record, "user_id", "")


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configura logging global da aplicação."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if log_format.lower() == "json":
        formatter = CustomJsonFormatter(
            fmt="%(timestamp)s %(level)s %(logger)s %(message)s %(trace_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | trace_id=%(trace_id)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    handler.addFilter(ContextFilter())
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level.upper() == "DEBUG" else logging.WARNING
    )
