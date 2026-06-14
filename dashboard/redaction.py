"""Redaction helpers for dashboard diagnostics."""

from __future__ import annotations

from collections.abc import Mapping


REDACTED = "[redacted]"
SECRET_KEY_HINTS = (
    "secret",
    "token",
    "password",
    "credential",
    "api_key",
    "apikey",
    "user_id",
    "account",
    "chat_id",
)


def looks_secret_key(key: str) -> bool:
    normalized = key.strip().replace("-", "_").lower()
    return any(hint in normalized for hint in SECRET_KEY_HINTS)


def redact_mapping(values: Mapping[str, object]) -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in values.items():
        if looks_secret_key(str(key)):
            redacted[str(key)] = REDACTED
        elif isinstance(value, Mapping):
            redacted[str(key)] = redact_mapping(value)
        else:
            redacted[str(key)] = value
    return redacted


def redact_text(text: str, *, secret_values: tuple[str, ...] = ()) -> str:
    redacted = str(text)
    for value in secret_values:
        if value:
            redacted = redacted.replace(value, REDACTED)
    for marker in SECRET_KEY_HINTS:
        redacted = redacted.replace(marker, REDACTED)
        redacted = redacted.replace(marker.upper(), REDACTED)
    return redacted
