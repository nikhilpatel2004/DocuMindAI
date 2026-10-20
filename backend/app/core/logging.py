"""Structured logging helpers.

Secrets (passwords, JWTs, API keys) are never logged. A redaction helper
scrubs common sensitive keys from log records.
"""
from __future__ import annotations

import logging
import re

REDACTED = "***REDACTED***"

# Keys whose values must never appear in logs.
_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "pwd",
    "token",
    "jwt",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "session",
}

# Regex used as a last-resort scrubber on string payloads.
_SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|pwd|token|jwt|secret|api[_-]?key|authorization|cookie)\s*[:=]\s*"
    r"[^,\s\"']+"
)


class RedactingFilter(logging.Filter):
    """Logging filter that redacts sensitive values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if isinstance(record.msg, str):
            record.msg = _SECRET_PATTERN.sub(r"\1=***REDACTED***", record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (REDACTED if str(k).lower() in _SENSITIVE_KEYS else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    REDACTED if isinstance(a, str) and "secret" in a.lower() else a
                    for a in record.args
                )
        return True


def setup_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_documind_configured", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    handler.addFilter(RedactingFilter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    root._documind_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance for the given name."""
    return logging.getLogger(name)


setup_logging()
