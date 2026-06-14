"""Telegram Bot API delivery boundary for notification-domain events."""

from __future__ import annotations

import os
import json
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping

import yaml

from marketpilot.notification_events import (
    NotificationDeduplicator,
    NotificationDomainEvent,
    NotificationRateLimiter,
)


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "notifications.yaml"
DEFAULT_TOKEN_ENV_VAR = "TELEGRAM_BOT_TOKEN"
DEFAULT_CHAT_ID_ENV_VAR = "TELEGRAM_CHAT_ID"

_SECRET_HINTS = ("secret", "token", "password", "credential", "api_key", "chat_id")
_ALLOWED_SECRET_REFERENCE_SUFFIXES = ("_env_var", "_secret_ref", "_secret_name")
PAPER_ONLY_WARNING = "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE"


class TelegramDeliveryStatus(str, Enum):
    DISABLED = "disabled"
    MISSING_TOKEN = "missing_token"
    MISSING_CHAT_ID = "missing_chat_id"
    DUPLICATE_SUPPRESSED = "duplicate_suppressed"
    RATE_LIMITED = "rate_limited"
    REJECTED = "rejected"
    FAILED = "failed"
    DELIVERED = "delivered"


@dataclass(frozen=True, repr=False)
class TelegramConfig:
    paper_trading_only: bool
    telegram_enabled: bool
    delivery_required_for_safety: bool
    token_env_var: str = DEFAULT_TOKEN_ENV_VAR
    chat_id_env_var: str = DEFAULT_CHAT_ID_ENV_VAR
    bot_token: str | None = field(default=None, repr=False)
    chat_id: str | None = field(default=None, repr=False)
    message_max_chars: int = 3900

    @property
    def missing_secret_names(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.bot_token:
            missing.append(self.token_env_var)
        if not self.chat_id:
            missing.append(self.chat_id_env_var)
        return tuple(missing)

    @property
    def can_deliver(self) -> bool:
        return self.telegram_enabled and self.bot_token is not None and self.chat_id is not None

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "paper_trading_only": self.paper_trading_only,
            "telegram_enabled": self.telegram_enabled,
            "delivery_required_for_safety": self.delivery_required_for_safety,
            "token_env_var": self.token_env_var,
            "chat_id_env_var": self.chat_id_env_var,
            "bot_token": "[redacted]" if self.bot_token else None,
            "chat_id": "[redacted]" if self.chat_id else None,
            "message_max_chars": self.message_max_chars,
        }

    def __repr__(self) -> str:
        safe = self.to_safe_dict()
        return f"TelegramConfig({safe!r})"


@dataclass(frozen=True, repr=False)
class TelegramDeliveryResult:
    status: TelegramDeliveryStatus
    event_type: str
    correlation_id: str
    detail: str = ""
    error_code: int | None = None
    retry_after_seconds: int | None = None
    telegram_message_id: str | None = None

    @property
    def delivered(self) -> bool:
        return self.status is TelegramDeliveryStatus.DELIVERED

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "detail": self.detail,
            "error_code": self.error_code,
            "retry_after_seconds": self.retry_after_seconds,
            "telegram_message_id": self.telegram_message_id,
        }

    def __repr__(self) -> str:
        return f"TelegramDeliveryResult({self.to_safe_dict()!r})"


TelegramHttpClient = Callable[..., Mapping[str, object]]


@dataclass
class TelegramDeliveryService:
    config: TelegramConfig
    http_client: TelegramHttpClient | None = None
    deduplicator: NotificationDeduplicator | None = None
    rate_limiter: NotificationRateLimiter | None = None
    timeout_seconds: int = 10

    def deliver(self, event: NotificationDomainEvent) -> TelegramDeliveryResult:
        if not self.config.telegram_enabled:
            return self._result(event, TelegramDeliveryStatus.DISABLED, "Telegram delivery is disabled.")
        if not self.config.bot_token:
            return self._result(event, TelegramDeliveryStatus.MISSING_TOKEN, f"Missing {self.config.token_env_var}.")
        if not self.config.chat_id:
            return self._result(event, TelegramDeliveryStatus.MISSING_CHAT_ID, f"Missing {self.config.chat_id_env_var}.")
        if self.deduplicator is not None and not self.deduplicator.should_emit(event):
            return self._result(event, TelegramDeliveryStatus.DUPLICATE_SUPPRESSED, "Duplicate event suppressed.")
        if self.rate_limiter is not None and not self.rate_limiter.allow(event.timestamp):
            return self._result(event, TelegramDeliveryStatus.RATE_LIMITED, "Local Telegram rate limit reached.")

        payload = {
            "chat_id": self.config.chat_id,
            "text": format_telegram_message(event, max_chars=self.config.message_max_chars),
            "disable_web_page_preview": True,
        }
        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"

        try:
            http_client = self.http_client or _post_json
            response = http_client(url=url, payload=payload, timeout_seconds=self.timeout_seconds)
        except Exception as exc:  # pragma: no cover - exercised by tests through public result
            return self._result(event, TelegramDeliveryStatus.FAILED, self._redact(str(exc)))

        return self._result_from_response(event, response)

    def _result_from_response(
        self,
        event: NotificationDomainEvent,
        response: Mapping[str, object],
    ) -> TelegramDeliveryResult:
        if not isinstance(response, Mapping):
            return self._result(event, TelegramDeliveryStatus.FAILED, "Telegram response was not a mapping.")

        if response.get("ok") is True:
            result = response.get("result")
            message_id = None
            if isinstance(result, Mapping) and result.get("message_id") is not None:
                message_id = str(result.get("message_id"))
            return self._result(event, TelegramDeliveryStatus.DELIVERED, "Delivered.", telegram_message_id=message_id)

        error_code = _to_optional_int(response.get("error_code"))
        description = self._redact(str(response.get("description") or "Telegram API rejected the message."))
        parameters = response.get("parameters")
        retry_after = None
        if isinstance(parameters, Mapping):
            retry_after = _to_optional_int(parameters.get("retry_after"))

        if error_code == 429 or retry_after is not None:
            return self._result(
                event,
                TelegramDeliveryStatus.RATE_LIMITED,
                description,
                error_code=error_code,
                retry_after_seconds=retry_after,
            )

        return self._result(event, TelegramDeliveryStatus.REJECTED, description, error_code=error_code)

    def _result(
        self,
        event: NotificationDomainEvent,
        status: TelegramDeliveryStatus,
        detail: str,
        *,
        error_code: int | None = None,
        retry_after_seconds: int | None = None,
        telegram_message_id: str | None = None,
    ) -> TelegramDeliveryResult:
        return TelegramDeliveryResult(
            status=status,
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            detail=self._redact(detail),
            error_code=error_code,
            retry_after_seconds=retry_after_seconds,
            telegram_message_id=telegram_message_id,
        )

    def _redact(self, text: str) -> str:
        redacted = text
        for value in (self.config.bot_token, self.config.chat_id):
            if value:
                redacted = redacted.replace(value, "[redacted]")
        return redacted


def format_telegram_message(event: NotificationDomainEvent, *, max_chars: int = 3900) -> str:
    """Format a concise plain-text Telegram message from a domain event."""

    lines = [
        PAPER_ONLY_WARNING,
        f"{event.severity.upper()} {event.event_type}",
        f"Correlation: {event.correlation_id}",
    ]
    ordered_keys = (
        "symbol",
        "setup",
        "classification",
        "score",
        "mode",
        "activation_state",
        "order_state",
        "fill_state",
        "stop",
        "target",
        "regime_state",
        "system_health",
        "reason",
    )
    for key in ordered_keys:
        if key in event.payload:
            value = event.payload[key]
            if not _looks_secret_key(key) and value != "[redacted]":
                lines.append(f"{_label(key)}: {_sanitize_message_value(value)}")

    text = "\n".join(lines)
    if len(text) > max_chars:
        return text[: max(0, max_chars - 3)].rstrip() + "..."
    return text


def load_telegram_config(
    path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    env: Mapping[str, str] | None = None,
) -> TelegramConfig:
    """Load Telegram notification settings without reading secrets from files."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("notifications config root must be a mapping.")

    raw = loaded.get("notifications")
    if not isinstance(raw, dict):
        raise ValueError("notifications section is required.")

    _validate_notifications_config(raw)

    secret_source = env if env is not None else os.environ
    token_env_var = str(raw.get("token_env_var", DEFAULT_TOKEN_ENV_VAR)).strip()
    chat_id_env_var = str(raw.get("chat_id_env_var", DEFAULT_CHAT_ID_ENV_VAR)).strip()
    message_max_chars = int(raw.get("message_max_chars", 3900))
    if not token_env_var:
        raise ValueError("notifications.token_env_var is required.")
    if not chat_id_env_var:
        raise ValueError("notifications.chat_id_env_var is required.")
    if message_max_chars <= 0 or message_max_chars > 4096:
        raise ValueError("notifications.message_max_chars must be between 1 and 4096.")

    bot_token = _blank_to_none(secret_source.get(token_env_var))
    chat_id = _blank_to_none(secret_source.get(chat_id_env_var))

    return TelegramConfig(
        paper_trading_only=True,
        telegram_enabled=raw.get("telegram_enabled") is True,
        delivery_required_for_safety=False,
        token_env_var=token_env_var,
        chat_id_env_var=chat_id_env_var,
        bot_token=bot_token,
        chat_id=chat_id,
        message_max_chars=message_max_chars,
    )


def _validate_notifications_config(raw: Mapping[object, object]) -> None:
    if raw.get("paper_trading_only") is not True:
        raise ValueError("notifications.paper_trading_only must be true.")
    if raw.get("delivery_required_for_safety") is not False:
        raise ValueError("notifications.delivery_required_for_safety must be false.")

    for key, value in raw.items():
        normalized = str(key).strip().replace("-", "_").lower()
        if _is_secret_reference_name(normalized):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"notifications.{normalized} must name an external secret reference.")
            continue
        if _looks_secret_key(normalized) and _has_value(value):
            raise ValueError(
                f"notifications.{normalized} must come from an external secret store, not repository config."
            )


def _is_secret_reference_name(key: str) -> bool:
    return any(key.endswith(suffix) for suffix in _ALLOWED_SECRET_REFERENCE_SUFFIXES)


def _looks_secret_key(key: str) -> bool:
    return any(hint in key for hint in _SECRET_HINTS)


def _has_value(value: object) -> bool:
    return value not in (None, "")


def _blank_to_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _post_json(*, url: str, payload: Mapping[str, object], timeout_seconds: int) -> Mapping[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _label(key: str) -> str:
    return key.replace("_", " ").title()


def _sanitize_message_value(value: object) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    for marker in _SECRET_HINTS:
        text = text.replace(marker, "[redacted]")
        text = text.replace(marker.upper(), "[redacted]")
    banned_claims = ("guaranteed profit", "guaranteed return", "risk-free")
    lowered = text.lower()
    if any(claim in lowered for claim in banned_claims):
        return "[removed unsafe claim]"
    return text


def _to_optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
