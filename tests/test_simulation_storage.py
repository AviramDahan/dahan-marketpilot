from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.internal_paper_simulator import close_simulated_position, initial_simulated_portfolio, open_simulated_position
from marketpilot.risk import RiskDecision
from marketpilot.simulation_storage import (
    SimulationJsonlStore,
    event_for_closed_trade,
    event_for_open_position,
    rebuild_portfolio_from_events,
)


NOW = datetime(2026, 6, 19, 14, 30, tzinfo=timezone.utc)


def _risk() -> RiskDecision:
    return RiskDecision(
        accepted=True,
        symbol="MSFT",
        primary_setup="relative_strength_leader",
        quantity=10,
        risk_amount=Decimal("1000"),
        allocation_amount=Decimal("1000"),
        rejection_reasons=(),
        evidence={},
    )


def test_simulation_jsonl_store_round_trips_events(tmp_path):
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
    store = SimulationJsonlStore(tmp_path / "simulation.jsonl")
    store.append(event_for_open_position(portfolio.open_positions[0]))

    events = store.read_events()

    assert len(events) == 1
    assert events[0].payload["product_mode"] == "simulation_only"
    assert events[0].payload["real_order"] is False


def test_rebuild_portfolio_from_events_deduplicates_open_events(tmp_path):
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
    event = event_for_open_position(portfolio.open_positions[0])

    rebuilt = rebuild_portfolio_from_events((event, event), starting_cash="10000")

    assert len(rebuilt.open_positions) == 1
    assert rebuilt.available_cash == Decimal("9000")


def test_rebuild_portfolio_from_open_and_close_events():
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

    rebuilt = rebuild_portfolio_from_events(
        (event_for_open_position(portfolio.open_positions[0]), event_for_closed_trade(closed.closed_trades[0])),
        starting_cash="10000",
    )

    assert rebuilt.open_positions == ()
    assert rebuilt.closed_trades[0].realized_pnl == Decimal("100")

