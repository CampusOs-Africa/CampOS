import contextvars
import logging
import sys
from typing import Any

from pythonjsonlogger import json as jsonlogger

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


class CampusOSJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["request_id"] = request_id_var.get()
        log_record["correlation_id"] = correlation_id_var.get()
        log_record["service"] = "campusos-backend"
        log_record["level"] = record.levelname
        log_record["logger"] = record.name


def configure_logging():
    formatter = CampusOSJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s %(request_id)s %(correlation_id)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("campusos")
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]
    root_logger.propagate = False
    return root_logger


def log_audit_event(
    action: str,
    actor_id: str,
    target_id: str,
    status: str,
    details: dict[str, Any] | None = None,
):
    """Emit a structured JSON audit log event."""
    logger = logging.getLogger("campusos.audit")
    logger.info(
        f"AUDIT_EVENT: {action}",
        extra={
            "audit": True,
            "action": action,
            "actor_id": actor_id,
            "target_id": target_id,
            "status": status,
            "details": details or {},
        },
    )
