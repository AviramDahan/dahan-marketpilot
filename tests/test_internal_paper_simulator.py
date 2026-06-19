from datetime import datetime, timezone
from decimal import Decimal

import pytest

from marketpilot.internal_paper_simulator import (
    SimulatedExitReason,
    close_positions_by_stop_target,
    close_simulated_position,
    initial_simulated_portfolio,
    mark_to_market,
    open_simulated_position,
    performance_summary,
)
from marketpilot.risk import RiskDecision


NOW = datetime(2026, 6, 19, 14, 30, tzinfo=timezone.utc)


def _risk(symbol="MSFT", quantity=10) -> RiskDecision:
    return RiskDecision(
        accepted=True,
        symbol=symbol,
        primary_setup="relative_strength_leader",
        quantity=quantity,
        risk_amount=Decimal("1000"),
        allocation_amount=Decimal("1000"),
        rejection_reasons=(),
        evidence={"portfolio_epoch": "sim-1"},
    )


def test_open_simulated_position_updates_cash_and_keeps_simulation_labels():
    portfolio = initial_simulated_portfolio("10000")

    updated = open_simulated_position(
        portfolio,
        risk_decision=_risk(),
        idempotency_key="sim-1",
        entry_price="100",
        stop_price="95",
        target_price="115",
        opened_at=NOW,
        correlation_id="scan-1",
    )

    assert updated.available_cash == Decimal("9000")
    assert updated.equity == Decimal("10000")
    assert updated.open_positions[0].evidence["real_order"] is False
    assert updated.open_positions[0].evidence["quantconnect_order"] is False


def test_mark_to_market_updates_unrealized_pnl_and_equity():
    portfolio = open_simulated_position(
        initial_simulated_portfolio("10000"),
        risk_decision=_risk(),
        idempotency_key="sim-1",
        entry_price="100",
        stop_price="95",
        target_price="115",
        opened_at=NOW,
        correlation_id="scan-1",
    )

    marked = mark_to_market(portfolio, {"MSFT": "110"})

    assert marked.unrealized_pnl == Decimal("100")
    assert marked.equity == Decimal("10100")


def test_stop_and_target_close_positions_with_realized_pnl():
    portfolio = open_simulated_position(
        initial_simulated_portfolio("10000"),
        risk_decision=_risk(),
        idempotency_key="sim-1",
        entry_price="100",
        stop_price="95",
        target_price="115",
        opened_at=NOW,
        correlation_id="scan-1",
    )

    stopped = close_positions_by_stop_target(portfolio, {"MSFT": "94"}, closed_at=NOW)

    assert stopped.open_positions == ()
    assert stopped.closed_trades[0].exit_reason is SimulatedExitReason.STOP_HIT
    assert stopped.closed_trades[0].realized_pnl == Decimal("-50")


def test_manual_close_and_performance_summary():
    portfolio = open_simulated_position(
        initial_simulated_portfolio("10000"),
        risk_decision=_risk(),
        idempotency_key="sim-1",
        entry_price="100",
        stop_price="95",
        target_price="115",
        opened_at=NOW,
        correlation_id="scan-1",
    )
    closed = close_simulated_position(portfolio, idempotency_key="sim-1", exit_price="110", closed_at=NOW)

    summary = performance_summary(closed)

    assert summary["closed_trade_count"] == 1
    assert summary["realized_pnl"] == "100"
    assert summary["win_rate"] == 100
    assert summary["real_orders"] is False
    assert summary["quantconnect_required"] is False


def test_duplicate_idempotency_key_rejected():
    portfolio = open_simulated_position(
        initial_simulated_portfolio("10000"),
        risk_decision=_risk(),
        idempotency_key="sim-1",
        entry_price="100",
        stop_price="95",
        target_price="115",
        opened_at=NOW,
        correlation_id="scan-1",
    )

    with pytest.raises(ValueError, match="duplicate"):
        open_simulated_position(
            portfolio,
            risk_decision=_risk(),
            idempotency_key="sim-1",
            entry_price="100",
            stop_price="95",
            target_price="115",
            opened_at=NOW,
            correlation_id="scan-1",
        )

