"""Audit-only candidate ranking and Combined Swing readiness gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from marketpilot.scoring import CandidateClassification, MarketPilotScore, ScoreComponent, load_scoring_config
from marketpilot.setups.base import NumericEvidence, SetupRejectionReason


@dataclass(frozen=True)
class RankedCandidate:
    symbol: str
    primary_setup: str
    supporting_setups: tuple[str, ...]
    total_score: float
    component_scores: tuple[ScoreComponent, ...]
    classification: CandidateClassification
    confidence: float
    evidence: tuple[NumericEvidence, ...]
    hard_rejections: tuple[SetupRejectionReason, ...]
    timing: object
    explanation: tuple[str, ...]


@dataclass(frozen=True)
class CombinedSwingReadiness:
    enabled: bool
    ready: bool
    unmet_reasons: tuple[str, ...] = field(default_factory=tuple)


def rank_candidates(scores: Iterable[MarketPilotScore]) -> tuple[RankedCandidate, ...]:
    grouped: dict[str, list[MarketPilotScore]] = {}
    for score in scores:
        grouped.setdefault(score.symbol.strip().upper(), []).append(score)

    candidates: list[RankedCandidate] = []
    for symbol, symbol_scores in grouped.items():
        ordered = sorted(symbol_scores, key=_sort_key, reverse=True)
        primary = ordered[0]
        supporting = tuple(score.setup_name for score in ordered[1:] if score.classification is not CandidateClassification.REJECTED)
        evidence = tuple(item for score in ordered for item in score.evidence)
        hard_rejections = tuple(reason for score in ordered for reason in score.hard_rejections)
        explanation = tuple(line for score in ordered for line in score.explanation)
        candidates.append(
            RankedCandidate(
                symbol=symbol,
                primary_setup=primary.setup_name,
                supporting_setups=supporting,
                total_score=primary.total_score,
                component_scores=primary.component_scores,
                classification=primary.classification,
                confidence=primary.confidence,
                evidence=evidence,
                hard_rejections=hard_rejections,
                timing=primary.timing,
                explanation=explanation,
            )
        )
    return tuple(sorted(candidates, key=lambda candidate: (candidate.total_score, candidate.confidence), reverse=True))


def evaluate_combined_swing_readiness(
    prerequisites: Mapping[str, bool] | None = None,
    config: dict | None = None,
) -> CombinedSwingReadiness:
    active_config = config or load_scoring_config()
    combined = active_config.get("combined_swing", {})
    enabled = combined.get("enabled") is True
    required = tuple(combined.get("required_prerequisites", ()))
    provided = prerequisites or {}
    unmet = tuple(name for name in required if provided.get(name) is not True)
    return CombinedSwingReadiness(enabled=enabled, ready=enabled and not unmet, unmet_reasons=unmet if not enabled or unmet else ())


def _sort_key(score: MarketPilotScore) -> tuple[float, float, float, float]:
    return (
        score.total_score,
        score.confidence,
        _component_raw(score, "risk_quality"),
        _component_raw(score, "relative_strength"),
    )


def _component_raw(score: MarketPilotScore, category: str) -> float:
    for component in score.component_scores:
        if component.category == category:
            return component.raw_score
    return 0.0
