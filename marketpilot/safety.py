"""Fail-closed safety validation for Dahan MarketPilot configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from marketpilot.constants import PAPER_TRADING_ONLY


SECRET_HINTS = ("secret", "token", "password", "credential", "api_key", "chat_id")

FORBIDDEN_TRUE_KEYS = {
    "broker",
    "brokerage",
    "real_broker",
    "real_broker_enabled",
    "live_money",
    "live_money_enabled",
    "live_trading",
    "live_trading_enabled",
    "production_trading",
    "real_money",
    "real_money_enabled",
    "leverage",
    "leverage_allowed",
    "margin",
    "margin_allowed",
    "short",
    "short_selling",
    "short_selling_allowed",
    "options",
    "options_allowed",
    "futures",
    "futures_allowed",
    "crypto",
    "cryptocurrency",
    "cryptocurrency_allowed",
    "forex",
    "forex_allowed",
    "manual_orders",
    "manual_order_controls",
    "manual_order_controls_enabled",
    "order_buttons",
    "dashboard_order_submission",
}

FORBIDDEN_SECRET_KEYS = {
    "broker_api_key",
    "broker_secret",
    "broker_password",
    "real_money_credentials",
}


@dataclass(frozen=True)
class SafetyIssue:
    """A sanitized validation issue safe for logs, tests, and UI surfaces."""

    path: str
    code: str
    message: str


class SafetyValidationError(ValueError):
    """Raised when configuration violates the paper-only safety contract."""

    def __init__(self, issues: Iterable[SafetyIssue]):
        self.issues = tuple(issues)
        summary = "; ".join(f"{issue.path}: {issue.message}" for issue in self.issues)
        super().__init__(summary or "Unsafe configuration rejected.")


def validate_paper_trading_constant() -> None:
    """Ensure the central guard has not been modified."""

    if PAPER_TRADING_ONLY is not True:
        raise SafetyValidationError(
            [
                SafetyIssue(
                    path="PAPER_TRADING_ONLY",
                    code="paper_guard_disabled",
                    message="Central paper-only guard must remain true.",
                )
            ]
        )


def validate_safety_config(config: dict[str, Any]) -> None:
    """Validate nested configuration and reject unsafe trading capabilities."""

    validate_paper_trading_constant()
    issues: list[SafetyIssue] = []

    for path, key, value in _walk_mapping(config):
        normalized = _normalize_key(key)

        if normalized == "paper_trading_only" and value is not True:
            issues.append(
                SafetyIssue(
                    path=path,
                    code="paper_trading_only_false",
                    message="paper_trading_only must be true.",
                )
            )

        if normalized in FORBIDDEN_TRUE_KEYS and _is_enabled(value):
            issues.append(
                SafetyIssue(
                    path=path,
                    code="unsafe_feature_enabled",
                    message=f"{normalized} is not allowed in simulated Paper Trading only mode.",
                )
            )

        if normalized in FORBIDDEN_SECRET_KEYS or _looks_secret_key(normalized):
            if _has_value(value):
                issues.append(
                    SafetyIssue(
                        path=path,
                        code="secret_like_value",
                        message=f"{normalized} must be stored outside repository configuration.",
                    )
                )

    if issues:
        raise SafetyValidationError(issues)


def _walk_mapping(value: Any, prefix: str = "") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, dict):
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            path = f"{prefix}.{key}" if prefix else key
            yield path, key, raw_value
            yield from _walk_mapping(raw_value, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_mapping(item, f"{prefix}[{index}]")


def _normalize_key(key: str) -> str:
    return key.strip().replace("-", "_").lower()


def _is_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "enabled", "on", "live", "real"}
    if isinstance(value, (dict, list, tuple, set)):
        return bool(value)
    return value is not None


def _looks_secret_key(key: str) -> bool:
    return any(hint in key for hint in SECRET_HINTS)


def _has_value(value: Any) -> bool:
    return value not in (None, "")
