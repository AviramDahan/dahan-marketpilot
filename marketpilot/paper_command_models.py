from __future__ import annotations

"""Pure command payload models for simulated QuantConnect paper trading."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.order_lifecycle import OrderIntent


COMMAND_TYPE_MARKETPILOT_SIGNAL = "marketpilot_signal"
ORDER_TAG_PREFIX = "mp"


@dataclass(frozen=True)
class DeploymentIdempotencyInput:
    project_id: int
    compile_id: str
    node_id: str
    version_id: str
    data_providers: Mapping[str, Mapping[str, object]]
    strategy_version: str
    config_version: str
    paper_trading_only: bool = PAPER_TRADING_ONLY

    def to_key_material(self) -> dict[str, object]:
        if self.paper_trading_only is not True:
            raise ValueError("paper_trading_only must be True for paper deployment keys.")
        return {
            "project_id": int(self.project_id),
            "compile_id": _required_text(self.compile_id, "compile_id"),
            "node_id": _required_text(self.node_id, "node_id"),
            "version_id": _required_text(self.version_id, "version_id"),
            "data_providers": _sorted_mapping(self.data_providers),
            "strategy_version": _required_text(self.strategy_version, "strategy_version"),
            "config_version": _required_text(self.config_version, "config_version"),
            "mode": "live-paper",
            "paper_trading_only": True,
        }


@dataclass(frozen=True)
class SignalFreshnessDecision:
    accepted: bool
    reason: str
    age_seconds: int | None = None


@dataclass(frozen=True)
class SignalFreshnessPolicy:
    ttl_seconds: int = 600

    def evaluate(
        self,
        *,
        signal_time_utc: datetime | None,
        expires_at_utc: datetime | None = None,
        now_utc: datetime | None = None,
    ) -> SignalFreshnessDecision:
        if self.ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive.")
        if signal_time_utc is None:
            return SignalFreshnessDecision(False, "missing_signal_time_utc")
        if signal_time_utc.tzinfo is None:
            return SignalFreshnessDecision(False, "naive_signal_time_utc")

        now = now_utc or datetime.now(timezone.utc)
        if now.tzinfo is None:
            return SignalFreshnessDecision(False, "naive_now_utc")

        signal_time = signal_time_utc.astimezone(timezone.utc)
        now = now.astimezone(timezone.utc)
        age_seconds = int((now - signal_time).total_seconds())
        if age_seconds < 0:
            return SignalFreshnessDecision(False, "future_signal_time", age_seconds)
        if age_seconds > self.ttl_seconds:
            return SignalFreshnessDecision(False, "stale_signal", age_seconds)

        if expires_at_utc is not None:
            if expires_at_utc.tzinfo is None:
                return SignalFreshnessDecision(False, "naive_expires_at_utc", age_seconds)
            expires_at = expires_at_utc.astimezone(timezone.utc)
            if expires_at < signal_time:
                return SignalFreshnessDecision(False, "expires_before_signal_time", age_seconds)
            if now > expires_at:
                return SignalFreshnessDecision(False, "expired_signal", age_seconds)

        return SignalFreshnessDecision(True, "fresh", age_seconds)


@dataclass(frozen=True)
class MarketPilotSignalCommand:
    correlation_id: str
    signal_id: str
    idempotency_key: str
    symbol: str
    quantity: int
    signal_time_utc: datetime
    expires_at_utc: datetime
    strategy_mode: str
    primary_setup: str
    paper_trading_only: bool = PAPER_TRADING_ONLY

    @classmethod
    def from_order_intent(
        cls,
        intent: OrderIntent,
        *,
        correlation_id: str,
        signal_id: str,
        expires_at_utc: datetime,
    ) -> MarketPilotSignalCommand:
        return cls(
            correlation_id=correlation_id,
            signal_id=signal_id,
            idempotency_key=intent.idempotency_key,
            symbol=intent.symbol,
            quantity=intent.quantity,
            signal_time_utc=intent.signal_time,
            expires_at_utc=expires_at_utc,
            strategy_mode=intent.strategy_mode,
            primary_setup=intent.primary_setup,
        )

    def to_payload(self) -> dict[str, object]:
        if self.paper_trading_only is not True:
            raise ValueError("paper_trading_only must be True for signal commands.")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive for signal commands.")
        signal_time = _required_aware_utc(self.signal_time_utc, "signal_time_utc")
        expires_at = _required_aware_utc(self.expires_at_utc, "expires_at_utc")
        if expires_at < signal_time:
            raise ValueError("expires_at_utc must be greater than or equal to signal_time_utc.")
        return {
            "command_type": COMMAND_TYPE_MARKETPILOT_SIGNAL,
            "correlation_id": _required_text(self.correlation_id, "correlation_id"),
            "signal_id": _required_text(self.signal_id, "signal_id"),
            "idempotency_key": _required_text(self.idempotency_key, "idempotency_key"),
            "symbol": _required_text(self.symbol, "symbol").upper(),
            "quantity": int(self.quantity),
            "signal_time_utc": signal_time.isoformat(),
            "expires_at_utc": expires_at.isoformat(),
            "strategy_mode": _required_text(self.strategy_mode, "strategy_mode"),
            "primary_setup": _required_text(self.primary_setup, "primary_setup"),
            "paper_trading_only": True,
            "command_delivery_is_order_execution": False,
        }


def build_deployment_idempotency_key(
    *,
    project_id: int,
    compile_id: str,
    node_id: str,
    version_id: str,
    data_providers: Mapping[str, Mapping[str, object]],
    strategy_version: str,
    config_version: str,
) -> str:
    inputs = DeploymentIdempotencyInput(
        project_id=project_id,
        compile_id=compile_id,
        node_id=node_id,
        version_id=version_id,
        data_providers=data_providers,
        strategy_version=strategy_version,
        config_version=config_version,
    )
    material = json.dumps(inputs.to_key_material(), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"paper-deploy-{digest}"


def build_order_tag(*, signal_id: str, idempotency_key: str) -> str:
    signal = _tag_part(signal_id, "signal_id")
    key = _tag_part(idempotency_key, "idempotency_key")
    tag = f"{ORDER_TAG_PREFIX}:{signal}:{key}"
    if len(tag) > 127:
        raise ValueError("order tag must be shorter than 128 characters.")
    return tag


def parse_order_tag(tag: str) -> dict[str, str] | None:
    parts = tag.split(":", 2)
    if len(parts) != 3 or parts[0] != ORDER_TAG_PREFIX or not parts[1] or not parts[2]:
        return None
    return {"signal_id": parts[1], "idempotency_key": parts[2]}


def _required_text(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} is required.")
    return text


def _required_aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _tag_part(value: str, field_name: str) -> str:
    text = _required_text(value, field_name)
    if ":" in text:
        raise ValueError(f"{field_name} must not contain ':'.")
    lowered = text.lower()
    if any(marker in lowered for marker in ("secret", "token", "password", "credential", "api_key")):
        raise ValueError(f"{field_name} must not contain credential-like text.")
    return text


def _sorted_mapping(value: Mapping[str, Mapping[str, object]]) -> dict[str, dict[str, object]]:
    if not value:
        raise ValueError("data_providers is required.")
    return {
        str(name): {str(key): provider[key] for key in sorted(provider)}
        for name, provider in sorted(value.items())
    }


__all__ = [
    "MarketPilotSignalCommand",
    "SignalFreshnessDecision",
    "SignalFreshnessPolicy",
    "build_deployment_idempotency_key",
    "build_order_tag",
    "parse_order_tag",
]
