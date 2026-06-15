"""Pure runtime orchestration contracts with no external side effects."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Callable, Mapping

from marketpilot.order_lifecycle import OrderIntent, make_order_idempotency_key
from marketpilot.ranking import RankedCandidate
from marketpilot.risk import RiskDecision
from marketpilot.setups.base import SetupResult, SetupTiming
from marketpilot.setups.relative_strength import (
    RelativeStrengthInput,
    evaluate_relative_strength_leader,
)
from marketpilot.setups.trend_pullback import TrendPullbackInput, evaluate_trend_pullback
from marketpilot.setups.volume_breakout import VolumeBreakoutInput, evaluate_volume_breakout
from marketpilot.timeframes import StrategyMode


class RuntimeOrchestrationStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_READY = "not_ready"
    BLOCKED = "blocked"
    SHADOW_ONLY = "shadow_only"
    PAPER_INTENT_READY = "paper_intent_ready"


class RuntimeSkippedReason(str, Enum):
    MISSING_RUNTIME_INPUT = "missing_runtime_input"
    QUANTCONNECT_AUTHORITY_MISSING = "quantconnect_authority_missing"
    SETUP_REGISTRY_EMPTY = "setup_registry_empty"
    NO_ELIGIBLE_SETUPS = "no_eligible_setups"
    RECONCILIATION_BLOCKED = "reconciliation_blocked"
    PAPER_MODE_NOT_ELIGIBLE = "paper_mode_not_eligible"
    RISK_REJECTED = "risk_rejected"
    ORDER_INTENT_NOT_CREATED = "order_intent_not_created"


class RuntimeAuthority(str, Enum):
    QUANTCONNECT = "quantconnect"
    LOCAL_MIRROR = "local_mirror"


SetupEvaluator = Callable[[object], SetupResult]


@dataclass(frozen=True)
class RuntimeSetupMetadata:
    setup_name: str
    evaluator: SetupEvaluator
    input_type: type
    enabled: bool = True
    paper_order_enabled: bool = False
    creates_scores: bool = False
    creates_orders: bool = False
    supports_strategy_modes: tuple[str, ...] = tuple(mode.value for mode in StrategyMode)


@dataclass(frozen=True)
class RuntimeOrchestrationInput:
    correlation_id: str
    strategy_mode: StrategyMode
    setup_results: tuple[SetupResult, ...]
    source_authority: RuntimeAuthority = RuntimeAuthority.QUANTCONNECT
    timing: SetupTiming | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeOrchestrationResult:
    status: RuntimeOrchestrationStatus
    correlation_id: str
    strategy_mode: StrategyMode
    source_authority: RuntimeAuthority = RuntimeAuthority.QUANTCONNECT
    skipped_reasons: tuple[RuntimeSkippedReason, ...] = field(default_factory=tuple)
    ranked_candidates: tuple[RankedCandidate, ...] = field(default_factory=tuple)
    risk_decisions: tuple[RiskDecision, ...] = field(default_factory=tuple)
    order_intents: tuple[OrderIntent, ...] = field(default_factory=tuple)
    notification_events: tuple[object, ...] = field(default_factory=tuple)
    evidence: Mapping[str, object] = field(default_factory=dict)
    executed_quantconnect_order_ids: tuple[str, ...] = field(default_factory=tuple)
    quantconnect_fill_ids: tuple[str, ...] = field(default_factory=tuple)
    quantconnect_backtest_id: str | None = None
    quantconnect_deployment_id: str | None = None
    authoritative_portfolio_state: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if self.executed_quantconnect_order_ids and self.authoritative_portfolio_state is None:
            raise ValueError("executed QuantConnect order ids require QuantConnect-authoritative portfolio state.")
        if self.quantconnect_fill_ids and self.authoritative_portfolio_state is None:
            raise ValueError("QuantConnect fill ids require QuantConnect-authoritative portfolio state.")
        if self.authoritative_portfolio_state is not None and self.source_authority is not RuntimeAuthority.QUANTCONNECT:
            raise ValueError("authoritative portfolio state must come from QuantConnect authority.")

        object.__setattr__(self, "evidence", _default_evidence(self) | dict(self.evidence))

    @classmethod
    def not_configured(
        cls,
        *,
        correlation_id: str,
        strategy_mode: StrategyMode,
        skipped_reasons: tuple[RuntimeSkippedReason, ...] = (),
        evidence: Mapping[str, object] | None = None,
    ) -> RuntimeOrchestrationResult:
        return cls(
            status=RuntimeOrchestrationStatus.NOT_CONFIGURED,
            correlation_id=correlation_id,
            strategy_mode=strategy_mode,
            skipped_reasons=skipped_reasons,
            evidence=evidence or {},
        )

    @classmethod
    def not_ready(
        cls,
        *,
        correlation_id: str,
        strategy_mode: StrategyMode,
        skipped_reasons: tuple[RuntimeSkippedReason, ...] = (),
        evidence: Mapping[str, object] | None = None,
    ) -> RuntimeOrchestrationResult:
        return cls(
            status=RuntimeOrchestrationStatus.NOT_READY,
            correlation_id=correlation_id,
            strategy_mode=strategy_mode,
            skipped_reasons=skipped_reasons,
            evidence=evidence or {},
        )

    @classmethod
    def blocked(
        cls,
        *,
        correlation_id: str,
        strategy_mode: StrategyMode,
        skipped_reasons: tuple[RuntimeSkippedReason, ...],
        evidence: Mapping[str, object] | None = None,
    ) -> RuntimeOrchestrationResult:
        return cls(
            status=RuntimeOrchestrationStatus.BLOCKED,
            correlation_id=correlation_id,
            strategy_mode=strategy_mode,
            skipped_reasons=skipped_reasons,
            evidence=evidence or {},
        )

    @classmethod
    def shadow_only(
        cls,
        *,
        correlation_id: str,
        strategy_mode: StrategyMode,
        ranked_candidates: tuple[RankedCandidate, ...] = (),
        risk_decisions: tuple[RiskDecision, ...] = (),
        notification_events: tuple[object, ...] = (),
        evidence: Mapping[str, object] | None = None,
    ) -> RuntimeOrchestrationResult:
        return cls(
            status=RuntimeOrchestrationStatus.SHADOW_ONLY,
            correlation_id=correlation_id,
            strategy_mode=strategy_mode,
            ranked_candidates=ranked_candidates,
            risk_decisions=risk_decisions,
            notification_events=notification_events,
            evidence=evidence or {},
        )

    @classmethod
    def paper_intent_ready(
        cls,
        *,
        correlation_id: str,
        strategy_mode: StrategyMode,
        ranked_candidates: tuple[RankedCandidate, ...] = (),
        risk_decisions: tuple[RiskDecision, ...] = (),
        order_intents: tuple[OrderIntent, ...] = (),
        notification_events: tuple[object, ...] = (),
        evidence: Mapping[str, object] | None = None,
    ) -> RuntimeOrchestrationResult:
        return cls(
            status=RuntimeOrchestrationStatus.PAPER_INTENT_READY,
            correlation_id=correlation_id,
            strategy_mode=strategy_mode,
            ranked_candidates=ranked_candidates,
            risk_decisions=risk_decisions,
            order_intents=order_intents,
            notification_events=notification_events,
            evidence=evidence or {},
        )


def get_default_setup_registry() -> dict[str, RuntimeSetupMetadata]:
    return {
        "trend_pullback": RuntimeSetupMetadata(
            setup_name="trend_pullback",
            evaluator=evaluate_trend_pullback,
            input_type=TrendPullbackInput,
        ),
        "volume_breakout": RuntimeSetupMetadata(
            setup_name="volume_breakout",
            evaluator=evaluate_volume_breakout,
            input_type=VolumeBreakoutInput,
        ),
        "relative_strength_leader": RuntimeSetupMetadata(
            setup_name="relative_strength_leader",
            evaluator=evaluate_relative_strength_leader,
            input_type=RelativeStrengthInput,
        ),
    }


def create_order_intent(
    *,
    candidate: RankedCandidate,
    risk_decision: RiskDecision,
    strategy_mode: StrategyMode,
    entry_price: Decimal,
    stop_price: Decimal | None,
    target_price: Decimal | None,
    portfolio_epoch: str,
) -> OrderIntent:
    signal_time = candidate.timing.signal_time
    idempotency_key = make_order_idempotency_key(
        symbol=candidate.symbol,
        strategy_mode=strategy_mode.value,
        primary_setup=candidate.primary_setup,
        signal_time=signal_time,
        portfolio_epoch=portfolio_epoch,
    )
    return OrderIntent(
        idempotency_key=idempotency_key,
        symbol=candidate.symbol,
        primary_setup=candidate.primary_setup,
        strategy_mode=strategy_mode.value,
        signal_time=signal_time,
        portfolio_epoch=portfolio_epoch,
        quantity=risk_decision.quantity,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        audit_metadata={
            "source_authority": RuntimeAuthority.QUANTCONNECT.value,
            "runtime_status": RuntimeOrchestrationStatus.PAPER_INTENT_READY.value,
            "risk_accepted": risk_decision.accepted,
            "classification_is_instruction": False,
        },
    )


def _default_evidence(result: RuntimeOrchestrationResult) -> dict[str, object]:
    return {
        "correlation_id": result.correlation_id,
        "strategy_mode": result.strategy_mode.value,
        "source_authority": result.source_authority.value,
        "paper_trading_only": True,
        "executes_orders": False,
        "creates_backtest_results": False,
        "telegram_delivery_required_for_safety": False,
        "dashboard_mutation_allowed": False,
    }


__all__ = [
    "RuntimeAuthority",
    "RuntimeOrchestrationInput",
    "RuntimeOrchestrationResult",
    "RuntimeOrchestrationStatus",
    "RuntimeSetupMetadata",
    "RuntimeSkippedReason",
    "create_order_intent",
    "get_default_setup_registry",
]
