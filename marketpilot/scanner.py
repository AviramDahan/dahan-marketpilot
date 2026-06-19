from __future__ import annotations

"""Simulation-only scanner engine over existing setup evaluators."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping

from marketpilot.product_modes import assert_simulation_only_safety
from marketpilot.ranking import RankedCandidate, rank_candidates
from marketpilot.runtime_orchestrator import RuntimeSetupMetadata, get_default_setup_registry
from marketpilot.scoring import GateStatus, MarketPilotScore, score_setup_result
from marketpilot.setups.base import SetupResult
from marketpilot.timeframes import StrategyMode
from marketpilot.universe_sources import UniverseSourceSnapshot


@dataclass(frozen=True)
class ScannerRejectedCandidate:
    symbol: str
    strategy_name: str
    reasons: tuple[str, ...]
    evidence: tuple[object, ...] = ()
    explanation: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScannerAcceptedCandidate:
    symbol: str
    strategy_name: str
    score: MarketPilotScore
    rank: int
    ranked_candidate: RankedCandidate


@dataclass(frozen=True)
class ScannerResult:
    correlation_id: str
    scanned_at: datetime
    strategy_mode: StrategyMode
    product_mode: str = "simulation_only"
    accepted_candidates: tuple[ScannerAcceptedCandidate, ...] = ()
    rejected_candidates: tuple[ScannerRejectedCandidate, ...] = ()
    ranked_candidates: tuple[RankedCandidate, ...] = ()
    setup_results: tuple[SetupResult, ...] = ()
    scores: tuple[MarketPilotScore, ...] = ()
    evidence: Mapping[str, object] = field(default_factory=dict)


def run_scanner(
    *,
    correlation_id: str,
    universe_snapshot: UniverseSourceSnapshot,
    setup_inputs: Mapping[tuple[str, str], object],
    strategy_mode: StrategyMode = StrategyMode.DAILY_ONLY,
    registry: Mapping[str, RuntimeSetupMetadata] | None = None,
    scanned_at: datetime | None = None,
) -> ScannerResult:
    assert_simulation_only_safety()
    clean_correlation = correlation_id.strip()
    if not clean_correlation:
        raise ValueError("correlation_id is required.")
    active_registry = dict(registry or get_default_setup_registry())
    accepted_symbols = set(universe_snapshot.accepted_symbols)
    rejected: list[ScannerRejectedCandidate] = []
    setup_results: list[SetupResult] = []

    for decision in universe_snapshot.universe.decisions:
        if decision.symbol not in accepted_symbols:
            rejected.append(
                ScannerRejectedCandidate(
                    symbol=decision.symbol,
                    strategy_name="universe",
                    reasons=tuple(issue.value for issue in decision.issues) or ("universe_rejected",),
                )
            )
            continue
        for setup_name, metadata in active_registry.items():
            if not metadata.enabled:
                continue
            setup_input = setup_inputs.get((decision.symbol, setup_name))
            if setup_input is None:
                rejected.append(
                    ScannerRejectedCandidate(
                        symbol=decision.symbol,
                        strategy_name=setup_name,
                        reasons=("setup_input_missing",),
                    )
                )
                continue
            result = metadata.evaluator(setup_input)
            setup_results.append(result)
            if not result.valid:
                rejected.append(
                    ScannerRejectedCandidate(
                        symbol=result.symbol,
                        strategy_name=result.setup_name,
                        reasons=tuple(reason.value for reason in result.rejection_reasons) or ("setup_rejected",),
                        evidence=result.evidence,
                        explanation=result.explanation,
                    )
                )

    gates = {
        "sector_fit": GateStatus.PASSED,
        "portfolio_gate": GateStatus.PASSED,
        "activation_gate": GateStatus.PASSED,
    }
    scores = tuple(score_setup_result(result, gate_statuses=gates) for result in setup_results if result.valid)
    ranked = rank_candidates(scores)
    accepted: list[ScannerAcceptedCandidate] = []
    for rank, candidate in enumerate(ranked, start=1):
        score = _score_for_candidate(scores, candidate)
        accepted.append(
            ScannerAcceptedCandidate(
                symbol=candidate.symbol,
                strategy_name=candidate.primary_setup,
                score=score,
                rank=rank,
                ranked_candidate=candidate,
            )
        )

    return ScannerResult(
        correlation_id=clean_correlation,
        scanned_at=_aware_utc(scanned_at or datetime.now(timezone.utc)),
        strategy_mode=strategy_mode,
        accepted_candidates=tuple(accepted),
        rejected_candidates=tuple(rejected),
        ranked_candidates=ranked,
        setup_results=tuple(setup_results),
        scores=scores,
        evidence={
            "product_mode": "simulation_only",
            "paper_trading_only": True,
            "quantconnect_required": False,
            "executes_orders": False,
            "universe_accepted_count": len(universe_snapshot.accepted_symbols),
            "universe_rejected_count": len(universe_snapshot.rejected_symbols),
        },
    )


def _score_for_candidate(scores: tuple[MarketPilotScore, ...], candidate: RankedCandidate) -> MarketPilotScore:
    for score in scores:
        if score.symbol.strip().upper() == candidate.symbol and score.setup_name == candidate.primary_setup:
            return score
    raise ValueError("ranked candidate score not found.")


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("scanner timestamp must be timezone-aware.")
    return value.astimezone(timezone.utc)


__all__ = [
    "ScannerAcceptedCandidate",
    "ScannerRejectedCandidate",
    "ScannerResult",
    "run_scanner",
]

