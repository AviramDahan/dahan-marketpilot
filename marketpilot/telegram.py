"""Telegram Bot API delivery boundary for notification-domain events."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "notifications.yaml"
DEFAULT_TOKEN_ENV_VAR = "TELEGRAM_BOT_TOKEN"
DEFAULT_CHAT_ID_ENV_VAR = "TELEGRAM_CHAT_ID"

_SECRET_HINTS = ("secret", "token", "password", "credential", "api_key", "chat_id")
_ALLOWED_SECRET_REFERENCE_SUFFIXES = ("_env_var", "_secret_ref", "_secret_name")


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
