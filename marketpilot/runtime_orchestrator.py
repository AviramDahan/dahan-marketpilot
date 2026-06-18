from __future__ import annotations

"""Pure runtime orchestration contracts with no external side effects."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Callable, Mapping

from marketpilot.notification_events import (
    NotificationDomainEvent,
    event_for_order_intent,
    event_for_risk_rejection,
    event_for_sizing_decision,
    event_for_system_incident,
)
from marketpilot.order_lifecycle import OrderIntent, make_order_idempotency_key
from marketpilot.paper_modes import PaperModeDecision, evaluate_paper_mode
from marketpilot.quantconnect_paper import QuantConnectPaperSnapshot
from marketpilot.ranking import RankedCandidate
from marketpilot.ranking import rank_candidates
from marketpilot.reconciliation import ReconciliationDecision, reconcile_quantconnect_state
from marketpilot.risk import PortfolioSnapshot, RiskDecision, evaluate_portfolio_risk
from marketpilot.scoring import CandidateClassification, GateStatus, MarketPilotScore, score_setup_result
from marketpilot.setups.base import SetupResult, SetupTiming
from marketpilot.setups.relative_strength import (
    RelativeStrengthInput,
    evaluate_relative_strength_leader,
)
from marketpilot.setups.trend_pullback import TrendPullbackInput, evaluate_trend_pullback
from marketpilot.setups.volume_breakout import VolumeBreakoutInput, evaluate_volume_breakout
from marketpilot.timeframes import StrategyMode
from marketpilot.validation import ValidationGateDecision


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
    validation_decision: ValidationGateDecision | None = None
    paper_mode_decision: PaperModeDecision | None = None
    quantconnect_snapshot: QuantConnectPaperSnapshot | None = None
    portfolio_snapshot: PortfolioSnapshot | None = None
    local_order_intents: tuple[OrderIntent, ...] = field(default_factory=tuple)
    local_lifecycle_events: tuple[object, ...] = field(default_factory=tuple)
    local_audit_records: tuple[Mapping[str, object], ...] = field(default_factory=tuple)
    existing_exit_obligations: tuple[Mapping[str, object], ...] = field(default_factory=tuple)
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
        ranked_candidates: tuple[RankedCandidate, ...] = (),
        risk_decisions: tuple[RiskDecision, ...] = (),
        notification_events: tuple[object, ...] = (),
        evidence: Mapping[str, object] | None = None,
    ) -> RuntimeOrchestrationResult:
        return cls(
            status=RuntimeOrchestrationStatus.BLOCKED,
            correlation_id=correlation_id,
            strategy_mode=strategy_mode,
            skipped_reasons=skipped_reasons,
            ranked_candidates=ranked_candidates,
            risk_decisions=risk_decisions,
            notification_events=notification_events,
            evidence=evidence or {},
        )

    @classmethod
    def shadow_only(
        cls,
        *,
        correlation_id: str,
        strategy_mode: StrategyMode,
        skipped_reasons: tuple[RuntimeSkippedReason, ...] = (),
        ranked_candidates: tuple[RankedCandidate, ...] = (),
        risk_decisions: tuple[RiskDecision, ...] = (),
        notification_events: tuple[object, ...] = (),
        evidence: Mapping[str, object] | None = None,
    ) -> RuntimeOrchestrationResult:
        return cls(
            status=RuntimeOrchestrationStatus.SHADOW_ONLY,
            correlation_id=correlation_id,
            strategy_mode=strategy_mode,
            skipped_reasons=skipped_reasons,
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


def run_runtime_pipeline(runtime_input: RuntimeOrchestrationInput) -> RuntimeOrchestrationResult:
    """Compose setup evidence into paper-only runtime intent evidence.

    This function is deliberately side-effect free. It never submits QuantConnect
    orders, never delivers Telegram messages, and never treats local mirrors as
    authoritative portfolio state.
    """

    correlation_id = runtime_input.correlation_id.strip()
    if not correlation_id:
        return RuntimeOrchestrationResult.not_configured(
            correlation_id="missing-correlation-id",
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.MISSING_RUNTIME_INPUT,),
            evidence={"missing_field": "correlation_id"},
        )

    valid_setups = tuple(setup for setup in runtime_input.setup_results if setup.valid)
    if not valid_setups:
        return RuntimeOrchestrationResult.not_ready(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.NO_ELIGIBLE_SETUPS,),
            evidence=_pipeline_evidence(runtime_input, reconciliation_status="not_evaluated"),
        )

    paper_decision = _paper_mode_decision(runtime_input)
    paper_order_eligible = bool(paper_decision and paper_decision.paper_order_eligible)
    qc_snapshot_available = runtime_input.quantconnect_snapshot is not None
    scoring_gates = _scoring_gate_statuses(paper_order_eligible=paper_order_eligible, qc_snapshot_available=qc_snapshot_available)
    scores = tuple(score_setup_result(setup, gate_statuses=scoring_gates) for setup in valid_setups)
    ranked = rank_candidates(scores)
    base_evidence = _pipeline_evidence(
        runtime_input,
        paper_decision=paper_decision,
        scores=scores,
        reconciliation_status="not_evaluated",
    )

    if not paper_order_eligible:
        skipped_reasons = [RuntimeSkippedReason.PAPER_MODE_NOT_ELIGIBLE]
        if runtime_input.quantconnect_snapshot is None:
            skipped_reasons.append(RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING)
        return RuntimeOrchestrationResult.shadow_only(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=tuple(skipped_reasons),
            ranked_candidates=ranked,
            evidence=base_evidence | {"paper_order_eligible": False},
        )

    if runtime_input.source_authority is not RuntimeAuthority.QUANTCONNECT:
        event = _system_event(
            correlation_id,
            reason="runtime_source_authority_not_quantconnect",
            block_new_entries=True,
            preserve_exits=True,
        )
        return RuntimeOrchestrationResult.blocked(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING,),
            evidence=base_evidence
            | {
                "reconciliation_status": "quantconnect_unavailable",
                "block_new_entries": True,
                "preserve_exits": True,
            },
            notification_events=(event,),
        )

    if runtime_input.quantconnect_snapshot is None:
        event = _system_event(
            correlation_id,
            reason="quantconnect_snapshot_missing",
            block_new_entries=True,
            preserve_exits=True,
        )
        return RuntimeOrchestrationResult.blocked(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING,),
            ranked_candidates=ranked,
            evidence=base_evidence
            | {
                "reconciliation_status": "quantconnect_unavailable",
                "block_new_entries": True,
                "preserve_exits": True,
            },
            notification_events=(event,),
        )

    reconciliation = reconcile_quantconnect_state(
        snapshot=runtime_input.quantconnect_snapshot,
        correlation_id=correlation_id,
        local_order_intents=runtime_input.local_order_intents,
        local_lifecycle_events=runtime_input.local_lifecycle_events,  # type: ignore[arg-type]
        local_audit_records=runtime_input.local_audit_records,
    )
    reconciliation_evidence = _reconciliation_evidence(reconciliation)
    if reconciliation.block_new_entries:
        event = _non_authoritative_event(reconciliation.system_event)
        return RuntimeOrchestrationResult.blocked(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.RECONCILIATION_BLOCKED,),
            ranked_candidates=ranked,
            evidence=base_evidence | reconciliation_evidence,
            notification_events=(event,) if event else (),
        )

    if runtime_input.portfolio_snapshot is None:
        event = _system_event(
            correlation_id,
            reason="quantconnect_authoritative_portfolio_snapshot_missing",
            block_new_entries=True,
            preserve_exits=True,
        )
        return RuntimeOrchestrationResult.blocked(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING,),
            ranked_candidates=ranked,
            evidence=base_evidence
            | reconciliation_evidence
            | {"portfolio_snapshot_available": False, "block_new_entries": True, "preserve_exits": True},
            notification_events=(event,),
        )

    risk_decisions: list[RiskDecision] = []
    order_intents: list[OrderIntent] = []
    events: list[NotificationDomainEvent] = []
    for candidate in _order_eligible_candidates(ranked):
        entry_price = _required_decimal(candidate.evidence, "planned_entry_price")
        stop_price = _required_decimal(candidate.evidence, "initial_stop_price")
        target_price = _optional_decimal(candidate.evidence, "target_price")
        reward_risk = _required_decimal(candidate.evidence, "reward_risk_proxy")
        sector = _evidence_string(candidate.evidence, "sector") or "unknown"
        risk = evaluate_portfolio_risk(
            candidate=candidate,
            portfolio=runtime_input.portfolio_snapshot,
            entry_price=entry_price,
            stop_distance=entry_price - stop_price,
            reward_risk=reward_risk,
            sector=sector,
            config=paper_decision.risk_config if paper_decision else None,
        )
        risk_decisions.append(risk)
        if not risk.accepted:
            events.append(_risk_rejection_event(correlation_id, risk))
            continue

        intent = create_order_intent(
            candidate=candidate,
            risk_decision=risk,
            strategy_mode=runtime_input.strategy_mode,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            portfolio_epoch=runtime_input.portfolio_snapshot.portfolio_epoch,
        )
        order_intents.append(intent)
        events.append(_sizing_event(correlation_id, risk))
        events.append(_order_intent_event(correlation_id, intent))

    if not risk_decisions:
        return RuntimeOrchestrationResult.shadow_only(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.ORDER_INTENT_NOT_CREATED,),
            ranked_candidates=ranked,
            evidence=base_evidence | reconciliation_evidence | {"paper_order_eligible": True},
        )

    if not order_intents:
        return RuntimeOrchestrationResult.blocked(
            correlation_id=correlation_id,
            strategy_mode=runtime_input.strategy_mode,
            skipped_reasons=(RuntimeSkippedReason.RISK_REJECTED,),
            ranked_candidates=ranked,
            risk_decisions=tuple(risk_decisions),
            evidence=base_evidence | reconciliation_evidence,
            notification_events=tuple(events),
        )

    return RuntimeOrchestrationResult.paper_intent_ready(
        correlation_id=correlation_id,
        strategy_mode=runtime_input.strategy_mode,
        ranked_candidates=ranked,
        risk_decisions=tuple(risk_decisions),
        order_intents=tuple(order_intents),
        notification_events=tuple(events),
        evidence=base_evidence | reconciliation_evidence | {"paper_order_eligible": True},
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


def _paper_mode_decision(runtime_input: RuntimeOrchestrationInput) -> PaperModeDecision | None:
    if runtime_input.paper_mode_decision is not None:
        return runtime_input.paper_mode_decision
    if runtime_input.validation_decision is None:
        return None
    return evaluate_paper_mode(validation_decision=runtime_input.validation_decision)


def _scoring_gate_statuses(*, paper_order_eligible: bool, qc_snapshot_available: bool) -> dict[str, GateStatus]:
    if paper_order_eligible and qc_snapshot_available:
        return {
            "sector_fit": GateStatus.PASSED,
            "portfolio_gate": GateStatus.PASSED,
            "activation_gate": GateStatus.PASSED,
        }
    return {
        "sector_fit": GateStatus.NOT_EVALUATED,
        "portfolio_gate": GateStatus.NOT_EVALUATED,
        "activation_gate": GateStatus.NOT_EVALUATED,
    }


def _pipeline_evidence(
    runtime_input: RuntimeOrchestrationInput,
    *,
    paper_decision: PaperModeDecision | None = None,
    scores: tuple[MarketPilotScore, ...] = (),
    reconciliation_status: str,
) -> dict[str, object]:
    evidence = {
        "classification_is_instruction": False,
        "authoritative_portfolio_source": RuntimeAuthority.QUANTCONNECT.value,
        "quantconnect_snapshot_available": runtime_input.quantconnect_snapshot is not None,
        "portfolio_snapshot_available": runtime_input.portfolio_snapshot is not None,
        "validation_state": runtime_input.validation_decision.state.value if runtime_input.validation_decision else "not_evaluated",
        "paper_mode": paper_decision.mode.value if paper_decision else "not_evaluated",
        "paper_order_eligible": bool(paper_decision and paper_decision.paper_order_eligible),
        "reconciliation_status": reconciliation_status,
        "block_new_entries": False,
        "preserve_exits": True,
        "existing_exit_obligations": runtime_input.existing_exit_obligations,
        "score_count": len(scores),
    }
    evidence.update(runtime_input.evidence)
    return evidence


def _reconciliation_evidence(decision: ReconciliationDecision) -> dict[str, object]:
    return {
        "reconciliation_status": "blocked" if decision.block_new_entries else "matched",
        "block_new_entries": decision.block_new_entries,
        "preserve_exits": decision.preserve_exits,
        "requires_explicit_recovery": decision.requires_explicit_recovery,
        "reconciliation_mismatch_types": tuple(mismatch.mismatch_type.value for mismatch in decision.mismatches),
        "authoritative_order_ids": dict(decision.authoritative_order_ids),
    }


def _order_eligible_candidates(candidates: tuple[RankedCandidate, ...]) -> tuple[RankedCandidate, ...]:
    return tuple(candidate for candidate in candidates if candidate.classification is CandidateClassification.BUY_CANDIDATE)


def _required_decimal(evidence: tuple[object, ...], name: str) -> Decimal:
    value = _evidence_value(evidence, name)
    if value is None:
        raise ValueError(f"{name} evidence is required for paper order intent readiness.")
    return Decimal(str(value))


def _optional_decimal(evidence: tuple[object, ...], name: str) -> Decimal | None:
    value = _evidence_value(evidence, name)
    return None if value is None else Decimal(str(value))


def _evidence_string(evidence: tuple[object, ...], name: str) -> str | None:
    value = _evidence_value(evidence, name)
    return None if value is None else str(value)


def _evidence_value(evidence: tuple[object, ...], name: str) -> object | None:
    for item in evidence:
        if getattr(item, "name", None) == name:
            return getattr(item, "value", None)
    return None


def _non_authoritative_event(event: NotificationDomainEvent | None) -> NotificationDomainEvent | None:
    if event is None:
        return None
    return NotificationDomainEvent.create(
        event.event_type,
        event.correlation_id,
        {
            **dict(event.payload),
            "controls_safety_logic": False,
            "delivery_required_for_safety": False,
        },
        severity=event.severity,
        timestamp=event.timestamp,
    )


def _system_event(
    correlation_id: str,
    *,
    reason: str,
    block_new_entries: bool,
    preserve_exits: bool,
) -> NotificationDomainEvent:
    return event_for_system_incident(
        correlation_id,
        {
            "authoritative_source": RuntimeAuthority.QUANTCONNECT.value,
            "reason": reason,
            "block_new_entries": block_new_entries,
            "preserve_exits": preserve_exits,
            "controls_safety_logic": False,
            "delivery_required_for_safety": False,
        },
        severity="high",
    )


def _risk_rejection_event(correlation_id: str, risk: RiskDecision) -> NotificationDomainEvent:
    return event_for_risk_rejection(
        correlation_id,
        {
            "symbol": risk.symbol,
            "primary_setup": risk.primary_setup,
            "rejection_reasons": tuple(reason.value for reason in risk.rejection_reasons),
            "controls_safety_logic": False,
            "delivery_required_for_safety": False,
        },
    )


def _sizing_event(correlation_id: str, risk: RiskDecision) -> NotificationDomainEvent:
    return event_for_sizing_decision(
        correlation_id,
        {
            "symbol": risk.symbol,
            "primary_setup": risk.primary_setup,
            "accepted": risk.accepted,
            "quantity": risk.quantity,
            "risk_amount": str(risk.risk_amount),
            "allocation_amount": str(risk.allocation_amount),
            "controls_safety_logic": False,
            "delivery_required_for_safety": False,
        },
    )


def _order_intent_event(correlation_id: str, intent: OrderIntent) -> NotificationDomainEvent:
    return event_for_order_intent(
        correlation_id,
        {
            "symbol": intent.symbol,
            "primary_setup": intent.primary_setup,
            "strategy_mode": intent.strategy_mode,
            "quantity": intent.quantity,
            "idempotency_key": intent.idempotency_key,
            "portfolio_epoch": intent.portfolio_epoch,
            "paper_trading_only": True,
            "submitted_to_quantconnect": False,
            "controls_safety_logic": False,
            "delivery_required_for_safety": False,
        },
    )


__all__ = [
    "RuntimeAuthority",
    "RuntimeOrchestrationInput",
    "RuntimeOrchestrationResult",
    "RuntimeOrchestrationStatus",
    "RuntimeSetupMetadata",
    "RuntimeSkippedReason",
    "create_order_intent",
    "get_default_setup_registry",
    "run_runtime_pipeline",
]
