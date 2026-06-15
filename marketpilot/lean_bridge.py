"""Safe LEAN adapter helpers for MarketPilot runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence

from marketpilot.data_quality import DataQualityStatus, UniverseCandidate
from marketpilot.indicators import IndicatorResult
from marketpilot.regime import BenchmarkSnapshot, RegimeResult, classify_market_regime
from marketpilot.runtime_orchestrator import (
    RuntimeOrchestrationInput,
    RuntimeOrchestrationResult,
    RuntimeSkippedReason,
    get_default_setup_registry,
    run_runtime_pipeline,
)
from marketpilot.setups.base import SetupResult
from marketpilot.symbol_data import SymbolData
from marketpilot.timeframes import (
    BarCompletionStatus,
    BarSessionMetadata,
    BarTimeframe,
    CompletedBar,
    StrategyMode,
)


DEFAULT_REQUIRED_INDICATORS = (
    "EMA20",
    "EMA50",
    "EMA200",
    "RSI14",
    "ATR14",
    "RS20",
    "RS60",
)


@dataclass(frozen=True)
class LeanBridgeReadiness:
    ready: bool
    reasons: tuple[str, ...] = ()


@dataclass
class LeanRuntimeBridge:
    """Hold LEAN-edge state and call pure MarketPilot runtime services."""

    strategy_mode: StrategyMode = StrategyMode.DAILY_ONLY
    required_indicators: tuple[str, ...] = DEFAULT_REQUIRED_INDICATORS
    symbol_data: dict[str, SymbolData] = field(default_factory=dict)
    setup_registry: Mapping[str, object] = field(default_factory=get_default_setup_registry)
    latest_dashboard_export: Mapping[str, object] = field(default_factory=dict)

    def select_dynamic_universe(self, coarse: Iterable[object]) -> list[object]:
        selected: list[object] = []
        decisions: list[Mapping[str, object]] = []
        for item in coarse:
            candidate = _coarse_to_universe_candidate(item)
            accepted = (
                candidate.price is not None
                and candidate.price >= 5
                and candidate.average_volume_20 is not None
                and candidate.average_volume_20 >= 500_000
                and candidate.average_dollar_volume_20 is not None
                and candidate.average_dollar_volume_20 >= 20_000_000
                and candidate.is_common_equity
                and not candidate.is_etf
                and not candidate.is_stale
                and candidate.is_supported
            )
            decisions.append(
                {
                    "symbol": candidate.normalized_symbol(),
                    "accepted": accepted,
                    "dynamic_universe": True,
                }
            )
            if accepted:
                selected.append(getattr(item, "Symbol", candidate.normalized_symbol()))

        self.latest_dashboard_export = {
            "dynamic_universe": {
                "status": "evaluated",
                "candidate_count": len(decisions),
                "selected_count": len(selected),
                "decisions": tuple(decisions),
            }
        }
        return selected

    def on_securities_changed(self, changes: object) -> tuple[str, ...]:
        removed_symbols: list[str] = []
        for security in _sequence_attr(changes, "RemovedSecurities", "removed_securities"):
            symbol = _symbol_value(security)
            if not symbol:
                continue
            removed_symbols.append(symbol)
            existing = self.symbol_data.get(symbol)
            if existing is not None:
                existing.mark_removed()
        return tuple(removed_symbols)

    def on_completed_bar(
        self,
        *,
        symbol: object,
        bar: CompletedBar,
        symbol_data: SymbolData | None = None,
        benchmark_snapshots: Sequence[BenchmarkSnapshot] = (),
        regime_result: RegimeResult | None = None,
        setup_results: Sequence[SetupResult] = (),
        required_indicators: Sequence[str] | None = None,
        correlation_id: str | None = None,
        strategy_mode: StrategyMode | None = None,
        runtime_evidence: Mapping[str, object] | None = None,
        quantconnect_snapshot: object | None = None,
        portfolio_snapshot: object | None = None,
        validation_decision: object | None = None,
        paper_mode_decision: object | None = None,
        local_order_intents: Sequence[object] = (),
        local_lifecycle_events: Sequence[object] = (),
        local_audit_records: Sequence[Mapping[str, object]] = (),
        existing_exit_obligations: Sequence[Mapping[str, object]] = (),
    ) -> RuntimeOrchestrationResult:
        normalized_symbol = _normalize_symbol(symbol)
        active_mode = strategy_mode or self.strategy_mode
        active_symbol_data = symbol_data or self.symbol_data.get(normalized_symbol)
        active_required = tuple(required_indicators or self.required_indicators)
        active_regime = regime_result
        if active_regime is None and benchmark_snapshots:
            active_regime = classify_market_regime(benchmark_snapshots)

        readiness = self.evaluate_readiness(
            bar=bar,
            symbol_data=active_symbol_data,
            required_indicators=active_required,
            benchmark_snapshots=benchmark_snapshots,
            regime_result=active_regime,
        )
        base_evidence = self._runtime_evidence(
            symbol=normalized_symbol,
            bar=bar,
            readiness=readiness,
            regime_result=active_regime,
            extra=runtime_evidence,
        )
        active_correlation_id = correlation_id or f"lean-{normalized_symbol}-{_timestamp_key(bar.time)}"

        if not readiness.ready:
            return RuntimeOrchestrationResult.not_ready(
                correlation_id=active_correlation_id,
                strategy_mode=active_mode,
                skipped_reasons=(RuntimeSkippedReason.MISSING_RUNTIME_INPUT,),
                evidence=base_evidence,
            )

        runtime_input = RuntimeOrchestrationInput(
            correlation_id=active_correlation_id,
            strategy_mode=active_mode,
            setup_results=tuple(setup_results),
            timing=next((setup.timing for setup in setup_results), None),
            validation_decision=validation_decision,  # type: ignore[arg-type]
            paper_mode_decision=paper_mode_decision,  # type: ignore[arg-type]
            quantconnect_snapshot=quantconnect_snapshot,  # type: ignore[arg-type]
            portfolio_snapshot=portfolio_snapshot,  # type: ignore[arg-type]
            local_order_intents=tuple(local_order_intents),  # type: ignore[arg-type]
            local_lifecycle_events=tuple(local_lifecycle_events),
            local_audit_records=tuple(local_audit_records),
            existing_exit_obligations=tuple(existing_exit_obligations),
            evidence=base_evidence,
        )
        result = run_runtime_pipeline(runtime_input)
        self.latest_dashboard_export = self.export_dashboard_evidence(result)
        return result

    def evaluate_readiness(
        self,
        *,
        bar: CompletedBar,
        symbol_data: SymbolData | None,
        required_indicators: Sequence[str],
        benchmark_snapshots: Sequence[BenchmarkSnapshot],
        regime_result: RegimeResult | None,
    ) -> LeanBridgeReadiness:
        reasons: list[str] = []
        if not bar.valid_for_signal():
            reasons.append("completed_bar_not_signal_valid")
        if symbol_data is None:
            reasons.append("missing_symbol_data")
        elif not symbol_data.future_signal_ready(tuple(required_indicators)):
            reasons.append("missing_indicator_readiness")
        if regime_result is None or not benchmark_snapshots:
            reasons.append("missing_benchmark_regime")
        return LeanBridgeReadiness(ready=not reasons, reasons=tuple(dict.fromkeys(reasons)))

    def export_dashboard_evidence(self, result: RuntimeOrchestrationResult | None) -> Mapping[str, object]:
        dashboard_export = {
            "status": "not_run",
            "reason": "operator_quantconnect_object_store_export_not_run",
            "source": "quantconnect_runtime_adapter",
            "paper_trading_only": True,
            "read_only_dashboard": True,
        }
        if result is None:
            return dashboard_export
        return dashboard_export | {
            "runtime_status": result.status.value,
            "ranked_candidates": len(result.ranked_candidates),
            "risk_decisions": len(result.risk_decisions),
            "order_intents": len(result.order_intents),
            "notification_events": len(result.notification_events),
            "paper_order_eligible": bool(result.evidence.get("paper_order_eligible", False)),
        }

    def _runtime_evidence(
        self,
        *,
        symbol: str,
        bar: CompletedBar,
        readiness: LeanBridgeReadiness,
        regime_result: RegimeResult | None,
        extra: Mapping[str, object] | None,
    ) -> dict[str, object]:
        evidence = {
            "adapter": "lean_bridge",
            "dynamic_universe": "lean_select_dynamic_universe",
            "readiness": "ready" if readiness.ready else "blocked",
            "readiness_reasons": readiness.reasons,
            "completed_bar_adapter": "quantconnect_like",
            "completed_bar_time": bar.time.isoformat(),
            "completed_bar_timeframe": bar.timeframe.value,
            "exchange_timezone": bar.session.exchange_timezone,
            "regular_hours": bar.session.regular_hours,
            "partial_session": bar.session.partial_session,
            "source_resolution": bar.session.source_resolution,
            "regime": regime_result.regime.value if regime_result else "not_ready",
            "indicators": "IndicatorResult",
            "setup_registry": tuple(sorted(self.setup_registry.keys())),
            "scoring_ranking": "runtime_orchestrator",
            "risk": "runtime_orchestrator",
            "reconciliation": "runtime_orchestrator",
            "paper_eligibility": "runtime_orchestrator",
            "notification_events": "runtime_orchestrator",
            "dashboard_export": self.export_dashboard_evidence(None),
            "external_quantconnect_execution": external_quantconnect_execution_evidence(),
            "symbol": symbol,
        }
        if extra:
            evidence.update(extra)
        return evidence


def initialize_runtime_bridge(*, strategy_mode: StrategyMode = StrategyMode.DAILY_ONLY) -> LeanRuntimeBridge:
    return LeanRuntimeBridge(strategy_mode=strategy_mode)


def map_quantconnect_bar_to_completed_bar(
    bar: object,
    *,
    timeframe: BarTimeframe = BarTimeframe.DAILY,
    exchange_timezone: str = "America/New_York",
    source_resolution: str | None = None,
    is_closed: bool = True,
    regular_hours: bool = True,
    partial_session: bool = False,
) -> CompletedBar:
    completion_status = BarCompletionStatus.COMPLETE
    if partial_session:
        completion_status = BarCompletionStatus.PARTIAL_SESSION
    elif not is_closed:
        completion_status = BarCompletionStatus.INCOMPLETE

    return CompletedBar(
        time=_datetime_attr(bar, "EndTime", "end_time", "Time", "time"),
        open=_float_attr(bar, "Open", "open"),
        high=_float_attr(bar, "High", "high"),
        low=_float_attr(bar, "Low", "low"),
        close=_float_attr(bar, "Close", "close"),
        volume=_float_attr(bar, "Volume", "volume"),
        timeframe=timeframe,
        completion_status=completion_status,
        session=BarSessionMetadata(
            exchange_timezone=exchange_timezone,
            regular_hours=regular_hours,
            partial_session=partial_session,
            source_resolution=source_resolution or timeframe.value,
        ),
    )


def external_quantconnect_execution_evidence() -> Mapping[str, object]:
    return {
        "status": "not_run",
        "reason": "external_quantconnect_operator_run_required",
        "executed": False,
        "submitted_orders": False,
        "paper_trading_only": True,
    }


def _coarse_to_universe_candidate(item: object) -> UniverseCandidate:
    price = _optional_float_attr(item, "Price", "price")
    volume = _optional_float_attr(item, "Volume", "volume")
    dollar_volume = _optional_float_attr(item, "DollarVolume", "dollar_volume")
    return UniverseCandidate(
        symbol=_normalize_symbol(getattr(item, "Symbol", getattr(item, "symbol", ""))),
        price=price,
        history_bars=int(_optional_float_attr(item, "HistoryBars", "history_bars") or 250),
        average_volume_20=volume,
        average_dollar_volume_20=dollar_volume if dollar_volume is not None else _dollar_volume(price, volume),
        market_cap=_optional_float_attr(item, "MarketCap", "market_cap"),
        sector=str(getattr(item, "Sector", getattr(item, "sector", "")) or "") or None,
        is_common_equity=bool(getattr(item, "IsCommonEquity", getattr(item, "is_common_equity", True))),
        is_etf=bool(getattr(item, "IsETF", getattr(item, "is_etf", False))),
        is_stale=bool(getattr(item, "IsStale", getattr(item, "is_stale", False))),
        is_supported=bool(getattr(item, "IsTradable", getattr(item, "is_supported", True))),
    )


def _dollar_volume(price: float | None, volume: float | None) -> float | None:
    if price is None or volume is None:
        return None
    return price * volume


def _sequence_attr(obj: object, *names: str) -> tuple[object, ...]:
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return tuple(value)
    return ()


def _symbol_value(security: object) -> str:
    return _normalize_symbol(getattr(security, "Symbol", getattr(security, "symbol", security)))


def _normalize_symbol(value: object) -> str:
    if hasattr(value, "Value"):
        value = getattr(value, "Value")
    if hasattr(value, "value"):
        value = getattr(value, "value")
    return str(value).strip().upper()


def _datetime_attr(obj: object, *names: str) -> datetime:
    for name in names:
        value = getattr(obj, name, None)
        if isinstance(value, datetime):
            return value
    return datetime.now(timezone.utc)


def _float_attr(obj: object, *names: str) -> float:
    value = _optional_float_attr(obj, *names)
    if value is None:
        raise ValueError(f"bar field is required: {names[0]}")
    return value


def _optional_float_attr(obj: object, *names: str) -> float | None:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is None:
                return None
            return float(value)
    return None


def _timestamp_key(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ") if value.tzinfo else value.strftime("%Y%m%dT%H%M%S")


__all__ = [
    "LeanBridgeReadiness",
    "LeanRuntimeBridge",
    "external_quantconnect_execution_evidence",
    "initialize_runtime_bridge",
    "map_quantconnect_bar_to_completed_bar",
]
