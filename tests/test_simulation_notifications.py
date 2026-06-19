from datetime import date

from marketpilot.simulation_notifications import (
    simulation_candidate_event,
    simulation_daily_summary_event,
    simulation_entry_event,
    simulation_exit_event,
    simulation_system_event,
)


def test_simulation_candidate_event_is_paper_only_and_not_order_authority():
    event = simulation_candidate_event(
        correlation_id="sim-1",
        candidate={"symbol": "MSFT", "score": 82},
    )

    assert event.event_type == "buy_candidate"
    assert event.payload["product_mode"] == "simulation_only"
    assert event.payload["paper_trading_only"] is True
    assert event.payload["real_order"] is False
    assert event.payload["quantconnect_order"] is False


def test_simulation_entry_exit_system_and_daily_summary_keep_simulation_labels():
    events = (
        simulation_entry_event(correlation_id="sim-1", position={"symbol": "MSFT", "quantity": 10}),
        simulation_exit_event(correlation_id="sim-1", trade={"symbol": "MSFT"}, exit_reason="target"),
        simulation_system_event(correlation_id="sim-1", status="ok", detail="heartbeat"),
        simulation_daily_summary_event(
            correlation_id="sim-1",
            summary_date=date(2026, 6, 19),
            new_candidates=1,
            entries=1,
            exits=1,
            open_positions=0,
        ),
    )

    assert [event.event_type for event in events] == ["paper_buy", "target", "system", "daily_summary"]
    assert all(event.payload["simulation_only"] is True for event in events)
    assert all(event.payload["delivery_required_for_safety"] is False for event in events)
    assert all(event.payload["not_financial_advice"] is True for event in events)
