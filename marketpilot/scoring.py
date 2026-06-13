"""Audit-only MarketPilot scoring for setup evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "scoring.yaml"
SCORE_CATEGORIES = (
    "trend_structure",
    "relative_strength",
    "momentum",
    "setup_quality",
    "volume_confirmation",
    "risk_quality",
)


class CandidateClassification(str, Enum):
    BUY_CANDIDATE = "BUY_CANDIDATE"
    WATCH = "WATCH"
    AVOID = "AVOID"
    REJECTED = "REJECTED"


class GateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_EVALUATED = "not_evaluated"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ScoreComponent:
    category: str
    raw_score: float
    weight: float
    weighted_score: float
    evidence: tuple[NumericEvidence, ...] = field(default_factory=tuple)
    passed: bool = True


@dataclass(frozen=True)
class MarketPilotScore:
    symbol: str
    setup_name: str
    total_score: float
    classification: CandidateClassification
    confidence: float
    component_scores: tuple[ScoreComponent, ...]
    evidence: tuple[NumericEvidence, ...]
    hard_rejections: tuple[SetupRejectionReason, ...]
    timing: object
    gate_statuses: Mapping[str, GateStatus]
    explanation: tuple[str, ...]


def load_scoring_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("scoring", loaded)
    if not isinstance(config, dict):
        raise ValueError("scoring config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("scoring config requires paper_trading_only: true.")
    weights = config.get("weights")
    if not isinstance(weights, dict):
        raise ValueError("scoring.weights must be a mapping.")
    if set(weights) != set(SCORE_CATEGORIES):
        raise ValueError("scoring.weights must define the shared score categories.")
    total = sum(float(weights[name]) for name in SCORE_CATEGORIES)
    if total != 100:
        raise ValueError("scoring weights must total 100.")
    disabled = config.get("disabled_behaviors", {})
    for key in ("create_orders", "portfolio_sizing", "backtest_result_creation", "telegram_delivery", "paper_deployment", "live_deployment"):
        if disabled.get(key) is not False:
            raise ValueError(f"scoring requires disabled {key}.")
    return config


def score_setup_result(
    setup_result: SetupResult,
    supporting_evidence: Sequence[NumericEvidence] = (),
    gate_statuses: Mapping[str, GateStatus | str] | None = None,
    config: dict | None = None,
) -> MarketPilotScore:
    active_config = config or load_scoring_config()
    evidence = tuple(setup_result.evidence) + tuple(supporting_evidence)
    gates = _normalize_gates(active_config, gate_statuses)
    components = tuple(_component_score(category, float(active_config["weights"][category]), evidence) for category in SCORE_CATEGORIES)
    required_failures = tuple(component.category for component in components if not component.passed)
    hard_rejections = setup_result.rejection_reasons
    total_score = round(sum(component.weighted_score for component in components), 2)
    confidence = _confidence(components, gates, setup_result)
    classification = _classification(total_score, confidence, hard_rejections, required_failures, evidence, gates, active_config)
    explanations = _explain(classification, hard_rejections, required_failures, gates)
    return MarketPilotScore(
        symbol=setup_result.symbol,
        setup_name=setup_result.setup_name,
        total_score=total_score,
        classification=classification,
        confidence=confidence,
        component_scores=components,
        evidence=evidence,
        hard_rejections=hard_rejections,
        timing=setup_result.timing,
        gate_statuses=gates,
        explanation=explanations,
    )


def _normalize_gates(config: dict, overrides: Mapping[str, GateStatus | str] | None) -> dict[str, GateStatus]:
    raw = dict(config.get("gates", {}))
    if overrides:
        raw.update(overrides)
    gates: dict[str, GateStatus] = {}
    for key in ("sector_fit", "portfolio_gate", "activation_gate"):
        value = raw.get(key, GateStatus.NOT_EVALUATED.value)
        gates[key] = value if isinstance(value, GateStatus) else GateStatus(str(value))
    return gates


def _component_score(category: str, weight: float, evidence: tuple[NumericEvidence, ...]) -> ScoreComponent:
    matched = tuple(item for item in evidence if _maps_to_category(category, item.name))
    if not matched:
        return ScoreComponent(category, 0.0, weight, 0.0, (), False)
    positive = [item for item in matched if item.passed is not False and item.value not in (None, "invalid")]
    raw_score = 100.0 * len(positive) / len(matched)
    weighted = round(raw_score * weight / 100, 2)
    return ScoreComponent(category, round(raw_score, 2), weight, weighted, matched, len(positive) > 0)


def _maps_to_category(category: str, name: str) -> bool:
    mapping = {
        "trend_structure": ("ema", "trend", "close_above", "52_week"),
        "relative_strength": ("rs", "relative_strength"),
        "momentum": ("momentum", "rsi", "macd", "roc"),
        "setup_quality": ("pullback", "breakout", "setup", "prior_resistance", "strategy_mode", "signal_timeframe"),
        "volume_confirmation": ("volume", "dollar_volume"),
        "risk_quality": ("risk", "reward", "atr", "extension", "regime"),
    }
    return any(token in name for token in mapping[category])


def _confidence(components: tuple[ScoreComponent, ...], gates: Mapping[str, GateStatus], setup_result: SetupResult) -> float:
    component_average = sum(component.raw_score for component in components) / len(components)
    gate_penalty = sum(10 for value in gates.values() if value in {GateStatus.NOT_EVALUATED, GateStatus.UNAVAILABLE})
    rejection_penalty = 25 if setup_result.rejection_reasons else 0
    timing_bonus = 5 if getattr(setup_result.timing, "later_valid_execution_required", False) else 0
    return max(0.0, min(100.0, round(component_average - gate_penalty - rejection_penalty + timing_bonus, 2)))


def _classification(
    total_score: float,
    confidence: float,
    hard_rejections: tuple[SetupRejectionReason, ...],
    required_failures: tuple[str, ...],
    evidence: tuple[NumericEvidence, ...],
    gates: Mapping[str, GateStatus],
    config: dict,
) -> CandidateClassification:
    if hard_rejections or required_failures:
        return CandidateClassification.REJECTED
    thresholds = config["classification"]
    reward_risk = _evidence_number(evidence, "reward_risk_proxy")
    regime_ok = _evidence_passed(evidence, "regime")
    portfolio_ok = gates["portfolio_gate"] is GateStatus.PASSED
    activation_ok = gates["activation_gate"] is GateStatus.PASSED
    if (
        total_score >= float(thresholds["buy_candidate_min_score"])
        and confidence >= float(thresholds["buy_candidate_min_confidence"])
        and regime_ok
        and reward_risk >= float(thresholds["min_reward_risk"])
        and portfolio_ok
        and activation_ok
    ):
        return CandidateClassification.BUY_CANDIDATE
    if total_score >= float(thresholds["watch_min_score"]):
        return CandidateClassification.WATCH
    return CandidateClassification.AVOID


def _evidence_number(evidence: tuple[NumericEvidence, ...], name: str) -> float:
    for item in evidence:
        if item.name == name and isinstance(item.value, (int, float)):
            return float(item.value)
    return 0.0


def _evidence_passed(evidence: tuple[NumericEvidence, ...], name: str) -> bool:
    for item in evidence:
        if item.name == name:
            return item.passed is not False
    return False


def _explain(
    classification: CandidateClassification,
    hard_rejections: tuple[SetupRejectionReason, ...],
    required_failures: tuple[str, ...],
    gates: Mapping[str, GateStatus],
) -> tuple[str, ...]:
    lines = [f"Classification: {classification.value}."]
    lines.extend(f"Hard rejection: {reason.value}." for reason in hard_rejections)
    lines.extend(f"Required scoring data failed: {failure}." for failure in required_failures)
    lines.extend(f"Gate {name}: {status.value}." for name, status in gates.items())
    return tuple(lines)
