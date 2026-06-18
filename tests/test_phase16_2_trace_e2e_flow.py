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
        "authority_endpoint": "/live/orders/read",
        "quantconnect_order_id": "1",
        "expected_order_tag": "mp:phase16-2-flow:order-1",
        "symbol": "SPY",
        "orders_authority_status": "filled",
        "filled_quantity": "1",
        "filled_at": "2026-06-17T18:01:00+00:00",
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


def test_trace_blocks_positive_filled_quantity_without_authoritative_metadata(tmp_path, capsys):
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
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert "qc_order_authority" in output["missing_segments"]


def test_trace_blocks_generic_filled_status_without_authoritative_metadata(tmp_path, capsys):
    evidence = {
        "status": "filled",
        "correlation_id": "phase16-2-flow",
        "signal_preview": {"signal_id": "phase16-2-flow"},
        "production_result": {"score": 91},
        "risk_decision": "accepted",
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
    assert "qc_order_authority" in output["missing_segments"]


def test_trace_blocks_missing_quantconnect_source(tmp_path, capsys):
    evidence = _complete_fill_evidence(source="local")
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert "qc_order_authority" in output["missing_segments"]


def test_trace_blocks_missing_live_orders_authority(tmp_path, capsys):
    evidence = _complete_fill_evidence()
    evidence.pop("authority_endpoint")
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert "qc_order_authority" in output["missing_segments"]


def test_trace_blocks_mismatched_correlation_tag(tmp_path, capsys):
    evidence = _complete_fill_evidence(expected_order_tag="mp:other:order-1")
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert "qc_order_authority" in output["missing_segments"]


def test_trace_blocks_missing_order_id_symbol_or_timestamp(tmp_path, capsys):
    for key in ("quantconnect_order_id", "symbol", "filled_at"):
        evidence = _complete_fill_evidence()
        evidence.pop(key)
        path = tmp_path / f"{key}.json"
        path.write_text(json.dumps(evidence), encoding="utf-8")

        result = phase16_2_trace_e2e_flow.main(["--evidence-json", str(path)])

        output = json.loads(capsys.readouterr().out)
        assert result == 2
        assert "qc_order_authority" in output["missing_segments"]


def test_trace_blocks_when_only_paper_flag_claims_risk_decision(tmp_path, capsys):
    evidence = {
        "status": "delivered",
        "correlation_id": "phase16-2-flow",
        "signal_preview": {"signal_id": "phase16-2-flow"},
        "production_result": {"score": 91},
        "orders_authority_status": "filled",
        "authority_endpoint": "/live/orders/read",
        "quantconnect_order_id": "1",
        "expected_order_tag": "mp:phase16-2-flow:order-1",
        "symbol": "SPY",
        "filled_quantity": "1",
        "filled_at": "2026-06-17T18:01:00+00:00",
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
        "authority_endpoint": "/live/orders/read",
        "quantconnect_order_id": "1",
        "expected_order_tag": "mp:phase16-2-a:order-1",
        "symbol": "SPY",
        "filled_quantity": "1",
        "filled_at": "2026-06-17T18:01:00+00:00",
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


def _complete_fill_evidence(**overrides):
    evidence = {
        "status": "delivered",
        "correlation_id": "phase16-2-flow",
        "signal_preview": {"signal_id": "phase16-2-flow"},
        "production_result": {"score": 91},
        "risk_decision": "accepted",
        "authority_endpoint": "/live/orders/read",
        "quantconnect_order_id": "1",
        "expected_order_tag": "mp:phase16-2-flow:order-1",
        "symbol": "SPY",
        "orders_authority_status": "filled",
        "filled_quantity": "1",
        "filled_at": "2026-06-17T18:01:00+00:00",
        "source": "quantconnect",
        "source_timestamp": "2026-06-17T18:00:00+00:00",
        "dashboard_url": "https://example.test",
        "telegram_message_id": "42",
        "paper_trading_only": True,
    }
    evidence.update(overrides)
    return evidence
