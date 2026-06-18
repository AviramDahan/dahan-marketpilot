from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from scripts import phase16_2_uat01_preflight


def test_preflight_reports_missing_env_without_values():
    result = phase16_2_uat01_preflight.run_preflight(
        env={},
        dashboard_url="https://example.test",
        heartbeat_url=None,
        shared_state_url=None,
        heartbeat_path=Path("missing.jsonl"),
        max_heartbeat_age_seconds=900,
        timeout_seconds=1,
    )

    assert result["status"] == "blocked_external_not_verified"
    assert result["checks"]["environment"]["missing"]
    assert result["checks"]["environment"]["values_printed"] is False
    assert result["controls_orders"] is False


def test_preflight_detects_temporary_probe_configuration():
    env = {
        "QUANTCONNECT_USER_ID": "configured",
        "QUANTCONNECT_API_TOKEN": "configured",
        "QC_PROJECT_ID": "123",
        "QC_DEPLOY_ID": "L-paper",
        "TELEGRAM_BOT_TOKEN": "configured",
        "TELEGRAM_CHAT_ID": "configured",
        "MARKETPILOT_RUNTIME_INPUT_KIND": "operator_paper_probe",
        "MARKETPILOT_OPERATOR_PAPER_PROBE_ENABLED": "true",
    }

    with (
        patch("scripts.phase16_2_uat01_preflight._check_quantconnect_deployment", return_value={"status": "passed"}),
        patch("scripts.phase16_2_uat01_preflight._check_telegram_configuration", return_value={"status": "passed"}),
        patch("scripts.phase16_2_uat01_preflight.observe_deployed_session", return_value={"status": "passed"}),
    ):
        result = phase16_2_uat01_preflight.run_preflight(
            env=env,
            dashboard_url="https://example.test",
            heartbeat_url="https://example.test/heartbeat",
            shared_state_url="https://example.test/dashboard-state",
            heartbeat_path=Path("missing.jsonl"),
            max_heartbeat_age_seconds=900,
            timeout_seconds=1,
        )

    assert result["status"] == "blocked_external_not_verified"
    assert result["checks"]["operator_probe_disabled"]["status"] == "temporary_uat_configuration_present"
    assert result["checks"]["operator_probe_disabled"]["restore_runtime_input_kind"] == "none"


def test_preflight_accepts_quantconnect_env_aliases():
    env = {
        "QUANTCONNECT_USER_ID": "configured",
        "QUANTCONNECT_API_TOKEN": "configured",
        "QUANTCONNECT_PROJECT_ID": "123",
        "QUANTCONNECT_LIVE_DEPLOY_ID": "L-paper",
        "TELEGRAM_BOT_TOKEN": "configured",
        "TELEGRAM_CHAT_ID": "configured",
    }

    check = phase16_2_uat01_preflight._check_environment(env)

    assert check["status"] == "passed"
    assert check["present"]["QC_PROJECT_ID|QUANTCONNECT_PROJECT_ID"] is True
    assert check["present"]["QC_DEPLOY_ID|QUANTCONNECT_LIVE_DEPLOY_ID"] is True


def test_reconciliation_check_passes_clean_fresh_sync():
    now = datetime.now(timezone.utc)
    result = phase16_2_uat01_preflight._check_reconciliation(
        {
            "sync_status": "success",
            "reconciliation_clean": True,
            "source": "quantconnect",
            "source_timestamp": now.isoformat(),
            "freshness_level": "fresh",
            "generation": 7,
        },
        max_age_seconds=900,
    )

    assert result["status"] == "passed"
    assert result["generation"] == 7


def test_reconciliation_check_blocks_unclean_missing_failed_stale_malformed_or_wrong_source():
    now = datetime.now(timezone.utc)
    cases = [
        {"sync_status": "success", "reconciliation_clean": False, "source": "quantconnect", "source_timestamp": now.isoformat(), "freshness_level": "fresh"},
        {"sync_status": "success", "source": "quantconnect", "source_timestamp": now.isoformat(), "freshness_level": "fresh"},
        {"sync_status": "api_error", "reconciliation_clean": True, "source": "quantconnect", "source_timestamp": now.isoformat(), "freshness_level": "fresh"},
        {"sync_status": "success", "reconciliation_clean": True, "source": "quantconnect", "source_timestamp": (now - timedelta(hours=1)).isoformat(), "freshness_level": "stale"},
        {"sync_status": "success", "reconciliation_clean": True, "source": "quantconnect", "source_timestamp": "not-a-time", "freshness_level": "fresh"},
        {"sync_status": "success", "reconciliation_clean": True, "source": "local", "source_timestamp": now.isoformat(), "freshness_level": "fresh"},
    ]

    for payload in cases:
        result = phase16_2_uat01_preflight._check_reconciliation(payload, max_age_seconds=900)
        assert result["status"] == "blocked_external_not_verified"


def test_probe_order_readiness_allows_no_orders_and_unrelated_protective_order():
    assert phase16_2_uat01_preflight.evaluate_probe_order_readiness(
        [],
        correlation_id="uat-cid",
        expected_order_tag="mp:uat-cid:order-1",
        idempotency_key="order-1",
        symbol="SPY",
        side="buy",
    )["readiness_decision"] == "passed"

    protective = SimpleNamespace(status="submitted", symbol="MSFT", quantity=-1, tag="protective-stop", idempotency_key="protective-msft", signal_id=None)
    result = phase16_2_uat01_preflight.evaluate_probe_order_readiness(
        [protective],
        correlation_id="uat-cid",
        expected_order_tag="mp:uat-cid:order-1",
        idempotency_key="order-1",
        symbol="SPY",
        side="buy",
    )

    assert result["readiness_decision"] == "passed"
    assert result["total_open_order_count"] == 1


def test_probe_order_readiness_blocks_matching_correlation_tag_duplicate_leftover_and_ambiguous():
    cases = [
        SimpleNamespace(status="submitted", symbol="SPY", quantity=1, tag="mp:other:order", idempotency_key="uat-cid", signal_id=None),
        SimpleNamespace(status="submitted", symbol="SPY", quantity=1, tag="mp:uat-cid:order-1", idempotency_key="other", signal_id=None),
        SimpleNamespace(status="submitted", symbol="SPY", quantity=1, tag="mp:other:order", idempotency_key="other", signal_id=None),
        SimpleNamespace(status="submitted", symbol="MSFT", quantity=1, tag="operator-probe-old", idempotency_key="old-probe", signal_id=None),
        SimpleNamespace(status="submitted", symbol="SPY", quantity=1, tag=None, idempotency_key=None, signal_id=None),
    ]

    for order in cases:
        result = phase16_2_uat01_preflight.evaluate_probe_order_readiness(
            [order],
            correlation_id="uat-cid",
            expected_order_tag="mp:uat-cid:order-1",
            idempotency_key="order-1",
            symbol="SPY",
            side="buy",
        )
        assert result["readiness_decision"] == "blocked"
        assert result["raw_orders_exposed"] is False


def test_check_quantconnect_deployment_resolves_legacy_aliases_and_reads_only():
    fake = _FakeQCApiClient()

    with patch("scripts.phase16_2_uat01_preflight.QCApiClient", return_value=fake):
        result = phase16_2_uat01_preflight._check_quantconnect_deployment(
            {
                "QC_PROJECT_ID": "123",
                "QC_DEPLOY_ID": "L-paper",
            }
        )

    assert result["status"] == "passed"
    assert result["values_printed"] is False
    assert fake.calls == [("read_live_algorithm", 123, "L-paper"), ("read_live_orders", 123, "L-paper")]


def test_check_quantconnect_deployment_resolves_deployed_aliases_and_fails_closed():
    fake = _FakeQCApiClient()

    with patch("scripts.phase16_2_uat01_preflight.QCApiClient", return_value=fake):
        result = phase16_2_uat01_preflight._check_quantconnect_deployment(
            {
                "QUANTCONNECT_PROJECT_ID": "456",
                "QUANTCONNECT_LIVE_DEPLOY_ID": "L-render",
            }
        )

    assert result["status"] == "passed"
    assert fake.calls == [("read_live_algorithm", 456, "L-render"), ("read_live_orders", 456, "L-render")]

    missing = phase16_2_uat01_preflight._check_quantconnect_deployment({})
    invalid = phase16_2_uat01_preflight._check_quantconnect_deployment({"QC_PROJECT_ID": "not-int", "QC_DEPLOY_ID": "L-paper"})
    assert missing["status"] == "failed"
    assert invalid["status"] == "failed"
    assert missing["values_printed"] is False
    assert invalid["values_printed"] is False


class _FakeQCApiClient:
    def __init__(self):
        self.calls = []

    def read_live_algorithm(self, *, project_id: int, deploy_id: str):
        self.calls.append(("read_live_algorithm", project_id, deploy_id))
        return QuantConnectPaperSnapshot(
            fixture_label=deploy_id,
            captured_at=datetime.now(timezone.utc),
            cash=Decimal("1000"),
            portfolio_equity=Decimal("1000"),
            holdings=(),
            orders=(),
            fills=(),
            deployment_status=QuantConnectDeploymentStatus.RUNNING,
            algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
            performance=QuantConnectPaperPerformance(total_orders=0, total_fills=0, unrealized_profit=Decimal("0")),
        )

    def read_live_orders(self, *, project_id: int, deploy_id: str):
        self.calls.append(("read_live_orders", project_id, deploy_id))
        return ()
