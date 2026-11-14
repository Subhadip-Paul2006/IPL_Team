"""Structured logging with automated secret masking."""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)Bearer\s+([A-Za-z0-9_\-\.]+)"),
    re.compile(
        r"(?i)(?:key|secret|password|token|credential|auth)\s*[:=]\s*(?:Bearer\s+)?['\"]?([^'\"\s,]+)['\"]?"
    ),
    re.compile(r"postgres(?:ql)?://[^:]+:([^@]+)@"),
    re.compile(r"(eyJ[A-Za-z0-9_\-\./=]+\.[A-Za-z0-9_\-\./=]+\.[A-Za-z0-9_\-\./=]+)"),
    re.compile(r"\b(sbp_[A-Za-z0-9_]+)\b"),
]

SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(?:(?:^|[_\-])(?:keys?|secrets?|passwords?|tokens?|credentials?|auth(?:entication|orization)?|api[_\-]?keys?)(?:$|[_\-])|(?:.*(?:password|secret|token|credential).*)|(?:api|private|client|access|refresh|jwt|auth|db)[_\-]?(?:key|secret|token|password|header))"
)


class SecretMaskingFilter(logging.Filter):
    """Logging filter that redacts secrets and sensitive credentials from log records."""

    def __init__(self, additional_secrets: list[str] | None = None) -> None:
        super().__init__()
        self.exact_secrets: set[str] = set()
        if additional_secrets:
            for s in additional_secrets:
                if s and len(s) > 4:
                    self.exact_secrets.add(s)

    def mask_text(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        result = text
        for secret in self.exact_secrets:
            result = result.replace(secret, "[REDACTED]")
        for pattern in SENSITIVE_PATTERNS:
            result = pattern.sub(
                lambda m: (
                    m.group(0).replace(m.group(1), "[REDACTED]") if m.lastindex else "[REDACTED]"
                ),
                result,
            )
        return result

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self.mask_text(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self.mask_text(v) if isinstance(v, str) else v for v in record.args
                )
        return True


class JsonFormatter(logging.Formatter):
    """Outputs log entries as structured JSON lines."""

    def __init__(self, mask_filter: SecretMaskingFilter | None = None) -> None:
        super().__init__()
        self.mask_filter = mask_filter or SecretMaskingFilter()

    def _sanitize(
        self,
        val: Any,
        key_name: str | None = None,
        seen: set[int] | None = None,
    ) -> Any:
        if seen is None:
            seen = set()

        if isinstance(val, (dict, list, tuple, set)):
            val_id = id(val)
            if val_id in seen:
                return "[CIRCULAR]"
            seen = seen | {val_id}

        if isinstance(val, str):
            masked = self.mask_filter.mask_text(val)
            if key_name and SENSITIVE_KEY_PATTERN.search(key_name) and "[REDACTED]" not in masked:
                return "[REDACTED]"
            return masked
        elif (
            isinstance(val, (int, float, bool))
            and key_name
            and SENSITIVE_KEY_PATTERN.search(key_name)
        ):
            return "[REDACTED]"
        elif isinstance(val, dict):
            return {k: self._sanitize(v, key_name=str(k), seen=seen) for k, v in val.items()}
        elif isinstance(val, (list, tuple, set)):
            return [self._sanitize(v, key_name=key_name, seen=seen) for v in val]
        return val

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.mask_filter.mask_text(record.getMessage()),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            raw_exc = self.formatException(record.exc_info)
            log_obj["exception"] = self.mask_filter.mask_text(raw_exc)
        elif record.exc_text:
            log_obj["exception"] = self.mask_filter.mask_text(record.exc_text)

        # Include custom extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "taskName",
            }:
                log_obj[key] = self._sanitize(value, key_name=key)
        return json.dumps(log_obj, default=str)


def setup_logging(
    log_level: str = "INFO",
    additional_secrets: list[str] | None = None,
) -> None:
    """Initialize structured logging with secret masking."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        handler = logging.StreamHandler()
        mask_filter = SecretMaskingFilter(additional_secrets=additional_secrets)
        handler.setFormatter(JsonFormatter(mask_filter=mask_filter))
        handler.addFilter(mask_filter)
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Retrieve a child logger under the rr_platform namespace."""
    return logging.getLogger(f"rr_platform.{name}")
