from datetime import datetime, timezone

from marketpilot.simulation_app import build_simulation_scan_payload


def test_simulation_app_builds_full_dashboard_payload_without_qc():
    payload = build_simulation_scan_payload("sim-run-1", datetime(2026, 6, 19, 14, 30, tzinfo=timezone.utc))

    assert payload["product_mode"] == "simulation_only"
    assert payload["paper_trading_only"] is True
    assert payload["real_orders"] is False
    assert payload["quantconnect_required"] is False
    assert payload["dashboard_mutation_allowed"] is False
    assert payload["guaranteed_profit_claims"] is False
    assert payload["live_brokerage_path"] is False
    assert payload["correlation_id"] == "sim-run-1"
    assert payload["candidates"]
    assert payload["open_trades"]
    assert payload["notifications"]
    assert payload["system"][0]["product_mode"] == "simulation_only"
    assert payload["notification_events"]
