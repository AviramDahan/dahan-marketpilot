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


def test_trace_redacts_secret_like_values():
    sanitized = phase16_2_trace_e2e_flow.sanitize(
        {
            "api_token": "abc",
            "detail": "token 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcde",
        }
    )

    assert sanitized["api_token"] == "[redacted]"
    assert "[redacted]" in sanitized["detail"]

