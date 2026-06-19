from __future__ import annotations

"""Composable simulation-only scanner application for deployed worker runs."""

from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Mapping

from marketpilot.dashboard_export import build_simulation_dashboard_payload
from marketpilot.internal_paper_simulator import initial_simulated_portfolio, open_simulated_position, performance_summary
from marketpilot.risk import PortfolioSnapshot, RiskDecision, evaluate_portfolio_risk
from marketpilot.runtime_orchestrator import RuntimeSetupMetadata
from marketpilot.scanner import ScannerAcceptedCandidate, ScannerRejectedCandidate, run_scanner
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.simulation_notifications import simulation_candidate_event, simulation_daily_summary_event, simulation_entry_event
from marketpilot.timeframes import StrategyMode
from marketpilot.universe_sources import (
    build_simulation_universe_snapshot,
    load_simulation_universe_config,
    load_universe_source_rows,
)
from marketpilot.universe import load_universe_config


STARTING_CASH = Decimal("100000")


def build_simulation_scan_payload(correlation_id: str, now: datetime) -> dict[str, object]:
    """Build one sanitized scanner/simulator dashboard payload."""

    scanned_at = _aware_utc(now)
    rows = load_universe_source_rows()
    universe_config = {**load_universe_config(), **_simulation_universe_overrides(load_simulation_universe_config())}
    universe = build_simulation_universe_snapshot(rows, universe_config=universe_config)
    setup_inputs = {
        (symbol, setup_name): (symbol, setup_name, _price_for_symbol(rows, symbol), _sector_for_symbol(rows, symbol))
        for symbol in universe.accepted_symbols
        for setup_name in ("trend_pullback", "volume_breakout", "relative_strength_leader")
    }
    scanner = run_scanner(
        correlation_id=correlation_id,
        universe_snapshot=universe,
        setup_inputs=setup_inputs,
        registry=_simulation_registry(),
        scanned_at=scanned_at,
    )
    portfolio = initial_simulated_portfolio(STARTING_CASH)
    notification_events = []
    risk_items = []
    if scanner.accepted_candidates:
        top = scanner.accepted_candidates[0]
        entry = Decimal(str(_price_for_symbol(rows, top.symbol)))
        stop = (entry * Decimal("0.95")).quantize(Decimal("0.01"))
        target = (entry * Decimal("1.125")).quantize(Decimal("0.01"))
        risk_decision = evaluate_portfolio_risk(
            candidate=top.ranked_candidate,
            portfolio=PortfolioSnapshot(
                simulated_equity=STARTING_CASH,
                available_cash=STARTING_CASH,
                portfolio_epoch=f"simulation:{correlation_id}",
            ),
            entry_price=entry,
            stop_distance=entry - stop,
            reward_risk=Decimal("2.5"),
            sector=_sector_for_symbol(rows, top.symbol),
        )
        risk_items.append(_risk_item(risk_decision))
        notification_events.append(
            simulation_candidate_event(correlation_id=correlation_id, candidate=_candidate_item(top))
        )
        if risk_decision.accepted:
            portfolio = open_simulated_position(
                portfolio,
                risk_decision=risk_decision,
                idempotency_key=f"{correlation_id}:{top.symbol}:{top.strategy_name}",
                entry_price=entry,
                stop_price=stop,
                target_price=target,
                opened_at=scanned_at,
                correlation_id=correlation_id,
                score=str(top.score.total_score),
                rank=top.rank,
                evidence={"scanner_rank": top.rank, "classification": top.score.classification.value},
            )
            notification_events.append(
                simulation_entry_event(
                    correlation_id=correlation_id,
                    position=_position_item(portfolio.open_positions[-1]),
                )
            )

    notification_events.append(
        simulation_daily_summary_event(
            correlation_id=correlation_id,
            summary_date=scanned_at.date(),
            new_candidates=len(scanner.accepted_candidates),
            entries=len(portfolio.open_positions),
            exits=len(portfolio.closed_trades),
            open_positions=len(portfolio.open_positions),
        )
    )
    notification_items = [_notification_item(event) for event in notification_events]
    payload = build_simulation_dashboard_payload(
        portfolio={
            "cash": str(portfolio.available_cash),
            "equity": str(portfolio.equity),
            "currency": "USD",
            "starting_cash": str(portfolio.starting_cash),
            "realized_pnl": str(portfolio.realized_pnl),
            "unrealized_pnl": str(portfolio.unrealized_pnl),
        },
        candidates=tuple(_candidate_item(candidate) for candidate in scanner.accepted_candidates),
        rejected_candidates=tuple(_rejected_item(candidate) for candidate in scanner.rejected_candidates),
        open_trades=tuple(_position_item(position) for position in portfolio.open_positions),
        closed_trades=tuple(_closed_trade_item(trade) for trade in portfolio.closed_trades),
        notifications=tuple(notification_items),
        activity=(
            {
                "record_type": "simulation_scan",
                "correlation_id": correlation_id,
                "accepted_candidates": len(scanner.accepted_candidates),
                "rejected_candidates": len(scanner.rejected_candidates),
                "paper_trading_only": True,
            },
        ),
        system=(
            {
                "name": "simulation_runner",
                "state": "ok",
                "correlation_id": correlation_id,
                "paper_trading_only": True,
                "product_mode": "simulation_only",
            },
        ),
        risk=tuple(risk_items),
        performance=performance_summary(portfolio),
        source_timestamp=scanned_at,
        fixture_label="simulation-runner",
    )
    payload.update(
        {
            "correlation_id": correlation_id,
            "notification_events": notification_events,
            "guaranteed_profit_claims": False,
            "live_brokerage_path": False,
        }
    )
    return payload


def _simulation_registry() -> dict[str, RuntimeSetupMetadata]:
    def evaluator(payload: object) -> SetupResult:
        symbol, setup_name, price, sector = payload  # type: ignore[misc]
        return _setup_result(str(symbol), str(setup_name), Decimal(str(price)), str(sector))

    return {
        "trend_pullback": RuntimeSetupMetadata("trend_pullback", evaluator, tuple),
        "volume_breakout": RuntimeSetupMetadata("volume_breakout", evaluator, tuple),
        "relative_strength_leader": RuntimeSetupMetadata("relative_strength_leader", evaluator, tuple),
    }


def _simulation_universe_overrides(config: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in config.items() if key not in {"symbols", "source"}}


def _setup_result(symbol: str, setup_name: str, price: Decimal, sector: str) -> SetupResult:
    signal_time = datetime.now(timezone.utc)
    return SetupResult(
        setup_name=setup_name,
        symbol=symbol,
        status=SetupStatus.VALID,
        timing=SetupTiming(signal_time=signal_time, strategy_mode=StrategyMode.DAILY_ONLY, bar_end=signal_time),
        evidence=(
            NumericEvidence("close_above_ema50", True, True, True),
            NumericEvidence("ema50_above_ema200", True, True, True),
            NumericEvidence("spy_rs20", 0.05, "> 0", True),
            NumericEvidence("spy_rs60", 0.08, "> 0", True),
            NumericEvidence("rsi14", 58, "supporting", True),
            NumericEvidence("breakout_close", float(price), float(price * Decimal("0.99")), True),
            NumericEvidence("volume_ratio", 2.0, 1.5, True),
            NumericEvidence("reward_risk_proxy", 2.5, 2.0, True),
            NumericEvidence("atr_pct", 4.0, 8.0, True),
            NumericEvidence("regime", "risk_on", "entry_allowed", True),
            NumericEvidence("planned_entry_price", float(price), "simulation_input", True),
            NumericEvidence("initial_stop_price", float(price * Decimal("0.95")), "simulation_input", True),
            NumericEvidence("target_price", float(price * Decimal("1.125")), "simulation_input", True),
            NumericEvidence("sector", sector, "simulation_universe", True),
        ),
        explanation=("deterministic simulation-only setup input",),
    )


def _candidate_item(candidate: ScannerAcceptedCandidate) -> dict[str, object]:
    return {
        "record_type": "scanner_candidate",
        "symbol": candidate.symbol,
        "strategy": candidate.strategy_name,
        "rank": candidate.rank,
        "score": candidate.score.total_score,
        "classification": candidate.score.classification.value,
        "confidence": candidate.score.confidence,
        "paper_trading_only": True,
        "product_mode": "simulation_only",
    }


def _rejected_item(candidate: ScannerRejectedCandidate) -> dict[str, object]:
    return {
        "record_type": "scanner_rejection",
        "symbol": candidate.symbol,
        "strategy": candidate.strategy_name,
        "reasons": candidate.reasons,
        "paper_trading_only": True,
        "product_mode": "simulation_only",
    }


def _risk_item(decision: RiskDecision) -> dict[str, object]:
    return {
        "record_type": "risk_decision",
        "symbol": decision.symbol,
        "strategy": decision.primary_setup,
        "state": "accepted" if decision.accepted else "rejected",
        "quantity": decision.quantity,
        "risk_amount": str(decision.risk_amount),
        "allocation_amount": str(decision.allocation_amount),
        "rejection_reasons": tuple(reason.value for reason in decision.rejection_reasons),
        "paper_trading_only": True,
        "product_mode": "simulation_only",
    }


def _position_item(position: object) -> dict[str, object]:
    data = asdict(position)
    return {
        "record_type": "simulated_open_trade",
        "symbol": data["symbol"],
        "strategy": data["strategy"],
        "state": data["status"].value,
        "quantity": data["quantity"],
        "entry_price": str(data["entry_price"]),
        "stop_price": str(data["stop_price"]),
        "target_price": str(data["target_price"]),
        "opened_at": data["opened_at"].isoformat(),
        "correlation_id": data["correlation_id"],
        "paper_trading_only": True,
        "product_mode": "simulation_only",
    }


def _closed_trade_item(trade: object) -> dict[str, object]:
    data = asdict(trade)
    return {
        "record_type": "simulated_closed_trade",
        "symbol": data["symbol"],
        "strategy": data["strategy"],
        "quantity": data["quantity"],
        "entry_price": str(data["entry_price"]),
        "exit_price": str(data["exit_price"]),
        "exit_reason": data["exit_reason"].value,
        "realized_pnl": str(data["realized_pnl"]),
        "closed_at": data["closed_at"].isoformat(),
        "correlation_id": data["correlation_id"],
        "paper_trading_only": True,
        "product_mode": "simulation_only",
    }


def _notification_item(event: object) -> dict[str, object]:
    return {
        "record_type": "simulation_notification",
        "event_type": getattr(event, "event_type", "unknown"),
        "correlation_id": getattr(event, "correlation_id", None),
        "severity": getattr(event, "severity", "info"),
        "paper_trading_only": True,
        "product_mode": "simulation_only",
    }


def _price_for_symbol(rows: tuple[object, ...], symbol: str) -> object:
    for row in rows:
        if getattr(row, "normalized_symbol") == symbol:
            return getattr(row, "price")
    raise ValueError(f"missing simulation price for {symbol}")


def _sector_for_symbol(rows: tuple[object, ...], symbol: str) -> str:
    for row in rows:
        if getattr(row, "normalized_symbol") == symbol:
            return str(getattr(row, "sector") or "unknown")
    return "unknown"


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("simulation app timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


__all__ = ["build_simulation_scan_payload"]
