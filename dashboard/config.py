"""Fail-closed dashboard runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml

from .redaction import REDACTED


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "dashboard.yaml"
DEFAULT_PASSWORD_ENV_VAR = "DASHBOARD_PASSWORD"
DEFAULT_ALLOWED_ACTIONS = ("view", "refresh", "login", "logout")
DEFAULT_NAVIGATION_SECTIONS = (
    "Overview",
    "Positions",
    "Trades",
    "Signals",
    "Backtests",
    "Strategies",
    "Risk",
    "Notifications",
    "Activity",
    "System Status",
)


@dataclass(frozen=True, repr=False)
class DashboardConfig:
    paper_trading_only: bool = True
    read_only: bool = True
    manual_order_controls_enabled: bool = False
    trading_currency: str = "USD"
    display_currency: str = "NIS"
    auth_enabled: bool = True
    password_env_var: str = DEFAULT_PASSWORD_ENV_VAR
    password: str | None = field(default=None, repr=False)
    allowed_actions: tuple[str, ...] = DEFAULT_ALLOWED_ACTIONS
    navigation_sections: tuple[str, ...] = DEFAULT_NAVIGATION_SECTIONS
    cache_ttl_seconds: int = 60
    stale_warning_seconds: int = 600
    stale_error_seconds: int = 1800
    gentle_poll_seconds: int = 120

    def __post_init__(self) -> None:
        object.__setattr__(self, "trading_currency", self.trading_currency.strip().upper())
        object.__setattr__(self, "display_currency", self.display_currency.strip().upper())
        object.__setattr__(self, "password_env_var", self.password_env_var.strip().upper())
        if self.paper_trading_only is not True:
            raise ValueError("dashboard.paper_trading_only must be true.")
        if self.read_only is not True:
            raise ValueError("dashboard.read_only must be true.")
        if self.manual_order_controls_enabled is not False:
            raise ValueError("dashboard.manual_order_controls_enabled must be false.")
        if self.trading_currency != "USD":
            raise ValueError("dashboard.trading_currency must be USD.")
        if self.display_currency != "NIS":
            raise ValueError("dashboard.display_currency must be NIS.")
        if self.auth_enabled is not True:
            raise ValueError("dashboard.auth_enabled must be true.")
        if not self.password_env_var:
            raise ValueError("dashboard.password_env_var is required.")
        if tuple(self.allowed_actions) != DEFAULT_ALLOWED_ACTIONS:
            raise ValueError("dashboard.allowed_actions must be view, refresh, login, logout.")
        if tuple(self.navigation_sections) != DEFAULT_NAVIGATION_SECTIONS:
            raise ValueError("dashboard.navigation_sections must match the approved operational sections.")
        if self.cache_ttl_seconds <= 0:
            raise ValueError("dashboard.cache_ttl_seconds must be positive.")
        if self.stale_warning_seconds <= self.cache_ttl_seconds:
            raise ValueError("dashboard.stale_warning_seconds must exceed cache_ttl_seconds.")
        if self.stale_error_seconds <= self.stale_warning_seconds:
            raise ValueError("dashboard.stale_error_seconds must exceed stale_warning_seconds.")
        if self.gentle_poll_seconds <= 0:
            raise ValueError("dashboard.gentle_poll_seconds must be positive.")

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "paper_trading_only": self.paper_trading_only,
            "read_only": self.read_only,
            "manual_order_controls_enabled": self.manual_order_controls_enabled,
            "trading_currency": self.trading_currency,
            "display_currency": self.display_currency,
            "auth_enabled": self.auth_enabled,
            "password_env_var": self.password_env_var,
            "password": REDACTED if self.password else None,
            "allowed_actions": self.allowed_actions,
            "navigation_sections": self.navigation_sections,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "stale_warning_seconds": self.stale_warning_seconds,
            "stale_error_seconds": self.stale_error_seconds,
            "gentle_poll_seconds": self.gentle_poll_seconds,
        }

    def __repr__(self) -> str:
        return f"DashboardConfig({self.to_safe_dict()!r})"


def load_dashboard_config(
    path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    env: Mapping[str, str] | None = None,
) -> DashboardConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("dashboard config root must be a mapping.")

    raw = loaded.get("dashboard")
    if not isinstance(raw, dict):
        raise ValueError("dashboard config must contain a dashboard mapping.")

    password_env_var = str(raw.get("password_env_var", DEFAULT_PASSWORD_ENV_VAR)).strip().upper()
    source = env if env is not None else os.environ
    password = _blank_to_none(source.get(password_env_var))
    _reject_raw_password_fields(raw)

    return DashboardConfig(
        paper_trading_only=raw.get("paper_trading_only") is True,
        read_only=raw.get("read_only") is True,
        manual_order_controls_enabled=raw.get("manual_order_controls_enabled") is True,
        trading_currency=str(raw.get("trading_currency") or ""),
        display_currency=str(raw.get("display_currency") or ""),
        auth_enabled=raw.get("auth_enabled") is True,
        password_env_var=password_env_var,
        password=password,
        allowed_actions=tuple(raw.get("allowed_actions") or ()),
        navigation_sections=tuple(raw.get("navigation_sections") or ()),
        cache_ttl_seconds=int(raw.get("cache_ttl_seconds", 60)),
        stale_warning_seconds=int(raw.get("stale_warning_seconds", 600)),
        stale_error_seconds=int(raw.get("stale_error_seconds", 1800)),
        gentle_poll_seconds=int(raw.get("gentle_poll_seconds", 120)),
    )


def _blank_to_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _reject_raw_password_fields(raw: Mapping[str, object]) -> None:
    for key in raw:
        normalized = str(key).strip().replace("-", "_").lower()
        if normalized in {"password", "dashboard_password", "auth_password"}:
            raise ValueError("dashboard password must come from an external environment variable.")
