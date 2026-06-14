"""Paper Trading activation modes and fail-closed eligibility decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Mapping

import yaml

from marketpilot.risk import RiskConfig, load_risk_config
from marketpilot.safety import validate_safety_config
from marketpilot.validation import ActivationApprovalState, ValidationGateDecision


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "paper_trading.yaml"


class PaperTradingMode(str, Enum):
    INACTIVE = "inactive"
    SHADOW = "shadow"
    LIMITED_PAPER = "limited_paper"
    FULL_PAPER = "full_paper"


@dataclass(frozen=True)
class PaperModeConfig:
    paper_trading_only: bool
    default_mode: PaperTradingMode
    limited_risk_config: RiskConfig
    full_risk_config: RiskConfig
    require_phase6_allocation_check: bool
    require_phase6_sector_check: bool
    require_phase6_reward_risk_check: bool
    require_phase6_stop_check: bool
    require_phase6_target_check: bool
    disabled_behaviors: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class PaperModeDecision:
    mode: PaperTradingMode
    activation_state: ActivationApprovalState
    paper_order_eligible: bool
    signal_preview_enabled: bool
    telegram_preview_enabled: bool
    risk_config: RiskConfig
    reasons: tuple[str, ...]
    required_phase6_checks: tuple[str, ...]


@dataclass(frozen=True)
class PaperModeTransition:
    prior_mode: PaperTradingMode
    requested_mode: PaperTradingMode
    resulting_mode: PaperTradingMode
    decision_reason: str
    timestamp: datetime
    correlation_id: str
    gate_evidence_summary: Mapping[str, object]
    reasons: tuple[str, ...]
    operator_payload: Mapping[str, object] = field(default_factory=dict)


def load_paper_mode_config(path: str | Path = DEFAULT_CONFIG_PATH) -> PaperModeConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("paper trading config must be a mapping.")
    validate_safety_config(loaded)
    config = loaded.get("paper_trading", loaded)
    if not isinstance(config, dict):
        raise ValueError("paper_trading config must be a mapping.")
    validate_safety_config(config)
    if config.get("paper_trading_only") is not True:
        raise ValueError("paper_trading.paper_trading_only must be true.")

    disabled = dict(config.get("disabled_behaviors") or {})
    for key in (
        "real_money_paths",
        "real_broker_adapters",
        "live_money_paths",
        "automatic_deployment",
        "telegram_delivery_required_for_safety",
        "fake_quantconnect_deployment_state",
        "fake_paper_portfolio_authority",
        "leverage",
        "margin",
        "short_selling",
        "options",
        "futures",
        "crypto",
        "forex",
    ):
        if disabled.get(key) is not False:
            raise ValueError(f"paper trading config requires disabled {key}.")

    phase6 = load_risk_config()
    limited_caps = config.get("limited_paper_caps")
    if not isinstance(limited_caps, dict):
        raise ValueError("limited_paper_caps section is required.")
    limited = RiskConfig(
        per_trade_risk_pct=_positive_decimal(limited_caps.get("per_trade_risk_pct"), "per_trade_risk_pct"),
        max_open_positions=_positive_int(limited_caps.get("max_open_positions"), "max_open_positions"),
        max_sector_exposure_pct=phase6.max_sector_exposure_pct,
        max_new_entries_per_day=_positive_int(
            limited_caps.get("max_new_entries_per_day"), "max_new_entries_per_day"
        ),
        max_position_allocation_pct=phase6.max_position_allocation_pct,
        minimum_reward_risk=phase6.minimum_reward_risk,
        minimum_quantity=phase6.minimum_quantity,
    )
    if limited.per_trade_risk_pct >= phase6.per_trade_risk_pct:
        raise ValueError("limited paper risk must be stricter than Phase 6 risk.")
    if limited.max_open_positions >= phase6.max_open_positions:
        raise ValueError("limited paper max open positions must be stricter than Phase 6 risk.")
    if limited.max_new_entries_per_day >= phase6.max_new_entries_per_day:
        raise ValueError("limited paper daily entries must be stricter than Phase 6 risk.")

    checks = config.get("required_phase6_checks")
    if not isinstance(checks, dict):
        raise ValueError("required_phase6_checks section is required.")
    required_check_names = (
        "allocation",
        "sector",
        "reward_risk",
        "stop",
        "target",
    )
    missing_checks = [name for name in required_check_names if checks.get(name) is not True]
    if missing_checks:
        raise ValueError(f"required Phase 6 checks must be enabled: {','.join(missing_checks)}.")

    return PaperModeConfig(
        paper_trading_only=True,
        default_mode=_mode(config.get("default_mode", PaperTradingMode.INACTIVE.value)),
        limited_risk_config=limited,
        full_risk_config=phase6,
        require_phase6_allocation_check=True,
        require_phase6_sector_check=True,
        require_phase6_reward_risk_check=True,
        require_phase6_stop_check=True,
        require_phase6_target_check=True,
        disabled_behaviors=disabled,
    )


def evaluate_paper_mode(
    *,
    validation_decision: ValidationGateDecision,
    config: PaperModeConfig | None = None,
) -> PaperModeDecision:
    active_config = config or load_paper_mode_config()
    required_checks = _required_checks(active_config)
    state = validation_decision.state
    failed_reasons = tuple(validation_decision.failed_gates)
    if failed_reasons:
        return PaperModeDecision(
            mode=PaperTradingMode.INACTIVE,
            activation_state=state,
            paper_order_eligible=False,
            signal_preview_enabled=False,
            telegram_preview_enabled=False,
            risk_config=active_config.limited_risk_config,
            reasons=failed_reasons,
            required_phase6_checks=required_checks,
        )

    if state is ActivationApprovalState.APPROVED_FOR_SHADOW:
        return PaperModeDecision(
            mode=PaperTradingMode.SHADOW,
            activation_state=state,
            paper_order_eligible=False,
            signal_preview_enabled=True,
            telegram_preview_enabled=True,
            risk_config=active_config.limited_risk_config,
            reasons=("shadow_preview_only",),
            required_phase6_checks=required_checks,
        )
    if state is ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER:
        return PaperModeDecision(
            mode=PaperTradingMode.LIMITED_PAPER,
            activation_state=state,
            paper_order_eligible=True,
            signal_preview_enabled=True,
            telegram_preview_enabled=True,
            risk_config=active_config.limited_risk_config,
            reasons=("limited_paper_caps_active",),
            required_phase6_checks=required_checks,
        )
    if state is ActivationApprovalState.APPROVED_FOR_FULL_PAPER:
        return PaperModeDecision(
            mode=PaperTradingMode.FULL_PAPER,
            activation_state=state,
            paper_order_eligible=True,
            signal_preview_enabled=True,
            telegram_preview_enabled=True,
            risk_config=active_config.full_risk_config,
            reasons=("full_phase6_risk_limits_active",),
            required_phase6_checks=required_checks,
        )

    reason = "explicit_paper_approval_required"
    if state in {ActivationApprovalState.UNVALIDATED, ActivationApprovalState.VALIDATION_FAILED}:
        reason = state.value
    return PaperModeDecision(
        mode=PaperTradingMode.INACTIVE,
        activation_state=state,
        paper_order_eligible=False,
        signal_preview_enabled=False,
        telegram_preview_enabled=False,
        risk_config=active_config.limited_risk_config,
        reasons=(reason,),
        required_phase6_checks=required_checks,
    )


def record_paper_mode_transition(
    *,
    prior_mode: PaperTradingMode | str,
    requested_mode: PaperTradingMode | str,
    validation_decision: ValidationGateDecision,
    timestamp: datetime | None = None,
    correlation_id: str,
    operator_payload: Mapping[str, object] | None = None,
    config: PaperModeConfig | None = None,
) -> PaperModeTransition:
    prior = _mode(prior_mode)
    requested = _mode(requested_mode)
    if not correlation_id.strip():
        raise ValueError("correlation_id is required for Paper mode transitions.")

    decision = evaluate_paper_mode(validation_decision=validation_decision, config=config)
    if requested is PaperTradingMode.INACTIVE:
        resulting = PaperTradingMode.INACTIVE
        decision_reason = "transition_approved"
        reasons = ("operator_requested_inactive",)
    elif requested is decision.mode:
        resulting = requested
        decision_reason = "transition_approved"
        reasons = decision.reasons
    else:
        resulting = prior
        decision_reason = "transition_rejected_fail_closed"
        reasons = (
            "requested_mode_not_allowed_by_activation_state",
            *decision.reasons,
        )

    return PaperModeTransition(
        prior_mode=prior,
        requested_mode=requested,
        resulting_mode=resulting,
        decision_reason=decision_reason,
        timestamp=timestamp or datetime.now(timezone.utc),
        correlation_id=correlation_id.strip(),
        gate_evidence_summary={
            "activation_state": validation_decision.state.value,
            "passed_gates": tuple(validation_decision.passed_gates),
            "failed_gates": tuple(validation_decision.failed_gates),
            "evaluated_mode": decision.mode.value,
            "paper_order_eligible": decision.paper_order_eligible,
        },
        reasons=tuple(dict.fromkeys(reasons)),
        operator_payload=_sanitize_payload(operator_payload or {}),
    )


def _required_checks(config: PaperModeConfig) -> tuple[str, ...]:
    checks = []
    if config.require_phase6_allocation_check:
        checks.append("phase6_allocation")
    if config.require_phase6_sector_check:
        checks.append("phase6_sector")
    if config.require_phase6_reward_risk_check:
        checks.append("phase6_reward_risk")
    if config.require_phase6_stop_check:
        checks.append("phase6_stop")
    if config.require_phase6_target_check:
        checks.append("phase6_target")
    return tuple(checks)


def _sanitize_payload(payload: Mapping[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in payload.items():
        lowered = key.lower()
        if any(marker in lowered for marker in ("secret", "token", "password", "credential", "api_key", "chat_id")):
            sanitized[key] = "[redacted]"
        else:
            sanitized[key] = value
    return sanitized


def _mode(value: object) -> PaperTradingMode:
    return value if isinstance(value, PaperTradingMode) else PaperTradingMode(str(value))


def _positive_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = Decimal(str(value))
    if decimal_value <= 0 or not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be a positive finite number.")
    return decimal_value


def _positive_int(value: object, field_name: str) -> int:
    try:
        int_value = int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc
    if int_value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return int_value
