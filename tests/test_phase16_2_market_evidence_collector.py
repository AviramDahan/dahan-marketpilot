import json

from scripts import phase16_2_market_evidence_collector
from scripts import phase16_2_trace_e2e_flow


def test_collector_blocks_missing_segments_without_fabricating(tmp_path, capsys):
    signal = tmp_path / "signal.json"
    signal.write_text(json.dumps({"signal_preview": {"signal_id": "uat-cid"}}), encoding="utf-8")

    result = phase16_2_market_evidence_collector.main(
        [
            "--correlation-id",
            "uat-cid",
            "--signal-json",
            str(signal),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert output["fabricated_segments"] == []
    assert output["segments"]["scoring"]["status"] == "not_run"


def test_collector_rejects_mismatched_correlation(tmp_path, capsys):
    signal = tmp_path / "signal.json"
    signal.write_text(json.dumps({"correlation_id": "other-cid", "signal_preview": {"signal_id": "other-cid"}}), encoding="utf-8")

    result = phase16_2_market_evidence_collector.main(
        [
            "--correlation-id",
            "uat-cid",
            "--signal-json",
            str(signal),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["segments"]["signal_or_probe"]["status"] == "correlation_mismatch"
    assert output["trace"]["missing_segments"]


def test_collector_output_is_trace_gate_compatible_when_complete(tmp_path, capsys):
    paths = {}
    payloads = {
        "signal": {"signal_preview": {"signal_id": "uat-cid"}},
        "scoring": {"correlation_id": "uat-cid", "production_result": {"score": 91}},
        "risk": {"correlation_id": "uat-cid", "risk_decision": "accepted"},
        "qc": {
            "correlation_id": "uat-cid",
            "authority_endpoint": "/live/orders/read",
            "quantconnect_order_id": "1",
            "expected_order_tag": "mp:uat-cid:order-1",
            "symbol": "SPY",
            "orders_authority_status": "filled",
            "filled_quantity": "1",
            "filled_at": "2026-06-17T18:01:00+00:00",
            "source": "quantconnect",
            "paper_trading_only": True,
        },
        "sync": {"correlation_id": "uat-cid", "source": "quantconnect", "source_timestamp": "2026-06-17T18:00:00+00:00"},
        "dashboard": {"correlation_id": "uat-cid", "dashboard_url": "https://example.test"},
        "telegram": {"correlation_id": "uat-cid", "status": "delivered", "telegram_message_id": "42"},
    }
    for name, payload in payloads.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = path
    output_path = tmp_path / "bundle.json"

    result = phase16_2_market_evidence_collector.main(
        [
            "--correlation-id",
            "uat-cid",
            "--signal-json",
            str(paths["signal"]),
            "--scoring-json",
            str(paths["scoring"]),
            "--risk-json",
            str(paths["risk"]),
            "--qc-orders-json",
            str(paths["qc"]),
            "--sync-json",
            str(paths["sync"]),
            "--dashboard-json",
            str(paths["dashboard"]),
            "--telegram-json",
            str(paths["telegram"]),
            "--output-json",
            str(output_path),
        ]
    )

    assert result == 0
    gate_result = phase16_2_trace_e2e_flow.build_trace([json.loads(output_path.read_text(encoding="utf-8"))])
    assert gate_result["status"] == "passed"
