from datetime import datetime, timezone

from scripts.phase16_3_simulation_evidence_report import evaluate_simulation_evidence


def _payload() -> dict[str, object]:
    return {
        "product_mode": "simulation_only",
        "paper_trading_only": True,
        "simulation_only": True,
        "read_only_dashboard": True,
        "dashboard_mutation_allowed": False,
        "real_orders": False,
        "quantconnect_required": False,
        "guaranteed_profit_claims": False,
        "live_brokerage_path": False,
        "source_timestamp": datetime(2026, 6, 19, 14, 30, tzinfo=timezone.utc).isoformat(),
        "portfolio": {"cash": "10000", "equity": "10025"},
        "candidates": [{"symbol": "MSFT"}],
        "rejected_candidates": [],
        "open_trades": [],
        "closed_trades": [],
        "notifications": [{"event_type": "daily_summary"}],
        "system": [{"name": "scheduler", "state": "ok"}],
    }


def test_simulation_evidence_report_passes_complete_sanitized_mvp_payload():
    report = evaluate_simulation_evidence(_payload())

    assert report["status"] == "passed"
    assert report["checks"]["no_secret_like_fields"] is True


def test_simulation_evidence_report_blocks_real_orders():
    payload = _payload()
    payload["real_orders"] = True

    report = evaluate_simulation_evidence(payload)

    assert report["status"] == "blocked_external_not_verified"
    assert report["checks"]["no_real_orders"] is False


def test_simulation_evidence_report_blocks_secret_like_fields():
    payload = _payload()
    payload["notifications"] = [{"telegram_token": "redacted-but-key-is-not-allowed"}]

    report = evaluate_simulation_evidence(payload)

    assert report["status"] == "blocked_external_not_verified"
    assert report["checks"]["no_secret_like_fields"] is False


def test_simulation_evidence_report_blocks_missing_timezone_timestamp():
    payload = _payload()
    payload["source_timestamp"] = "2026-06-19T14:30:00"

    report = evaluate_simulation_evidence(payload)

    assert report["status"] == "blocked_external_not_verified"
    assert report["checks"]["source_timestamp_timezone_aware"] is False
