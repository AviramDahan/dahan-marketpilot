import json

from scripts import phase16_2_trace_e2e_flow


def test_trace_blocks_when_segments_are_missing(capsys):
    result = phase16_2_trace_e2e_flow.main([])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert "qc_order_authority" in output["missing_segments"]
    assert output["paper_trading_only"] is True


def test_trace_passes_with_all_required_segments(tmp_path, capsys):
    evidence = {
        "status": "delivered",
        "correlation_id": "phase16-2-flow",
        "signal_preview": {"signal_id": "phase16-2-flow"},
        "production_result": {"score": 91},
        "risk_decision": "accepted",
        "orders_authority_status": "filled",
        "source": "quantconnect",
        "source_timestamp": "2026-06-17T18:00:00+00:00",
        "dashboard_url": "https://example.test",
        "telegram_message_id": "42",
        "paper_trading_only": True,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["missing_segments"] == []
    assert output["segment_correlation_ids"] == ["phase16-2-flow"]
    assert output["correlation_mismatch"] is False


def test_trace_blocks_rejected_order_as_partial_authority_only(tmp_path, capsys):
    evidence = {
        "status": "delivered",
        "correlation_id": "phase16-2-flow",
        "signal_preview": {"signal_id": "phase16-2-flow"},
        "production_result": {"score": 91},
        "risk_decision": "accepted",
        "orders_authority_status": "rejected",
        "source": "quantconnect",
        "source_timestamp": "2026-06-17T18:00:00+00:00",
        "dashboard_url": "https://example.test",
        "telegram_message_id": "42",
        "paper_trading_only": True,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert "qc_order_authority" in output["missing_segments"]
    assert output["partial_segments"]["qc_order_authority"]["status"] == "partial"


def test_trace_accepts_positive_filled_quantity_as_fill_authority(tmp_path, capsys):
    evidence = {
        "status": "delivered",
        "correlation_id": "phase16-2-flow",
        "signal_preview": {"signal_id": "phase16-2-flow"},
        "production_result": {"score": 91},
        "risk_decision": "accepted",
        "orders_authority_status": "submitted",
        "filled_quantity": "1",
        "source": "quantconnect",
        "source_timestamp": "2026-06-17T18:00:00+00:00",
        "dashboard_url": "https://example.test",
        "telegram_message_id": "42",
        "paper_trading_only": True,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"


def test_trace_blocks_when_only_paper_flag_claims_risk_decision(tmp_path, capsys):
    evidence = {
        "status": "delivered",
        "correlation_id": "phase16-2-flow",
        "signal_preview": {"signal_id": "phase16-2-flow"},
        "production_result": {"score": 91},
        "orders_authority_status": "filled",
        "source": "quantconnect",
        "source_timestamp": "2026-06-17T18:00:00+00:00",
        "dashboard_url": "https://example.test",
        "telegram_message_id": "42",
        "paper_trading_only": True,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert "risk_decision" in output["missing_segments"]


def test_trace_blocks_when_segments_have_different_correlation_ids(tmp_path, capsys):
    shared = {
        "status": "delivered",
        "signal_preview": {"signal_id": "phase16-2-a"},
        "production_result": {"score": 91},
        "risk_decision": {"accepted": True},
        "orders_authority_status": "filled",
        "source": "quantconnect",
        "source_timestamp": "2026-06-17T18:00:00+00:00",
        "dashboard_url": "https://example.test",
        "telegram_message_id": "42",
        "paper_trading_only": True,
    }
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps({"correlation_id": "phase16-2-a", **shared}), encoding="utf-8")
    second.write_text(json.dumps({"correlation_id": "phase16-2-b", **shared}), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(first), "--evidence-json", str(second)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert output["correlation_mismatch"] is True


def test_trace_redacts_secret_like_values():
    sanitized = phase16_2_trace_e2e_flow.sanitize(
        {
            "api_token": "abc",
            "detail": "token 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcde",
        }
    )

    assert sanitized["api_token"] == "[redacted]"
    assert "[redacted]" in sanitized["detail"]
