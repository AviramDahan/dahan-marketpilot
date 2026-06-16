"""Tests for marketpilot.qc_api — QC API client with safety guarantees."""

from __future__ import annotations

import json
import logging
import os
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from marketpilot.qc_api import (
    CredentialRedactionFilter,
    QCApiClient,
    QCApiConfig,
    QCApiError,
    QCAuthenticationError,
    QCClientError,
    QCNetworkError,
    QCRateLimitError,
    QCSafetyError,
    QCServerError,
    _ALLOWED_ENDPOINTS,
    _PAPER_GATED_ENDPOINTS,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "qc_api"
QC_COMMAND_SMOKE = Path(__file__).resolve().parents[1] / "scripts" / "qc_command_smoke.py"
QC_DISPATCH_PROBE = Path(__file__).resolve().parents[1] / "scripts" / "qc_command_dispatch_probe.py"
QC_OBJECT_STORE_SMOKE = Path(__file__).resolve().parents[1] / "scripts" / "qc_object_store_signal_smoke.py"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


def _make_client_with_mocked_auth() -> QCApiClient:
    """Create a QCApiClient that skips real credential validation."""
    config = QCApiConfig(user_id="99999", api_token="FAKE-TOKEN-DO-NOT-USE")
    with patch.object(QCApiClient, "_validate_credentials"):
        return QCApiClient(config=config)


def _load_qc_command_smoke_module():
    spec = importlib.util.spec_from_file_location("qc_command_smoke_test_module", QC_COMMAND_SMOKE)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_qc_dispatch_probe_module():
    spec = importlib.util.spec_from_file_location("qc_dispatch_probe_test_module", QC_DISPATCH_PROBE)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_qc_object_store_smoke_module():
    spec = importlib.util.spec_from_file_location("qc_object_store_smoke_test_module", QC_OBJECT_STORE_SMOKE)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# API-01 — HMAC Authentication
# ---------------------------------------------------------------------------


def test_hmac_auth_generates_authorization_and_timestamp_headers():
    client = _make_client_with_mocked_auth()
    headers = client._get_auth_headers()
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Basic ")
    assert "Timestamp" in headers
    assert headers["Timestamp"].isdigit()


def test_missing_env_vars_raises_authentication_error():
    env = {k: v for k, v in os.environ.items() if "QUANTCONNECT" not in k}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(QCAuthenticationError, match="QUANTCONNECT_USER_ID"):
            QCApiClient(config=None)


def test_invalid_credentials_fail_at_startup():
    config = QCApiConfig(user_id="99999", api_token="BAD-TOKEN")
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = '{"success": false}'
    with patch("requests.Session.get", return_value=mock_resp):
        with pytest.raises(QCAuthenticationError, match="authentication failed"):
            QCApiClient(config=config)


# ---------------------------------------------------------------------------
# API-02 — Safety Gate
# ---------------------------------------------------------------------------


def test_safety_gate_blocks_unknown_endpoint():
    client = _make_client_with_mocked_auth()
    with pytest.raises(QCSafetyError, match="not in the safety allowlist"):
        client._validate_endpoint("live/deploy")


def test_safety_gate_allows_read_endpoints():
    client = _make_client_with_mocked_auth()
    # Should not raise
    client._validate_endpoint("live/read")
    client._validate_endpoint("live/logs/read")
    client._validate_endpoint("authenticate")
    client._validate_endpoint("backtests/read")
    client._validate_endpoint("compile/create")
    client._validate_endpoint("compile/read")
    client._validate_endpoint("files/read")
    client._validate_endpoint("files/update")
    client._validate_endpoint("account/read")
    client._validate_endpoint("object/get")
    client._validate_endpoint("object/list")
    client._validate_endpoint("object/properties")


def test_safety_gate_blocks_paper_gated_when_constant_false():
    client = _make_client_with_mocked_auth()
    import marketpilot.qc_api as qc_mod

    original = qc_mod.PAPER_TRADING_ONLY
    try:
        qc_mod.PAPER_TRADING_ONLY = False
        with pytest.raises(QCSafetyError, match="PAPER_TRADING_ONLY must be True"):
            client._validate_endpoint("live/create")
        with pytest.raises(QCSafetyError, match="PAPER_TRADING_ONLY must be True"):
            client._validate_endpoint("live/commands/create")
        with pytest.raises(QCSafetyError, match="PAPER_TRADING_ONLY must be True"):
            client._validate_endpoint("live/orders/read")
    finally:
        qc_mod.PAPER_TRADING_ONLY = original


def test_safety_gate_allows_paper_gated_when_constant_true():
    client = _make_client_with_mocked_auth()
    # Should not raise — PAPER_TRADING_ONLY is True
    client._validate_endpoint("live/create")
    client._validate_endpoint("live/commands/create")
    client._validate_endpoint("live/orders/read")
    client._validate_endpoint("live/update/stop")
    client._validate_endpoint("live/update/liquidate")
    client._validate_endpoint("object/set")
    client._validate_endpoint("object/delete")


# ---------------------------------------------------------------------------
# API-03 — Retry Logic
# ---------------------------------------------------------------------------


def test_retry_on_429_rate_limit():
    client = _make_client_with_mocked_auth()
    call_count = {"n": 0}

    def side_effect(endpoint, payload=None):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise QCRateLimitError("rate limited", status_code=429)
        return {"success": True}

    with patch.object(client, "_validate_endpoint"):
        with patch.object(client, "_get_auth_headers", return_value={"Authorization": "Basic x", "Timestamp": "1"}):
            with patch("requests.Session.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"success": True}
                # Use the actual retry by patching at the session level
                responses = [
                    MagicMock(status_code=429, text="rate limited"),
                    MagicMock(status_code=429, text="rate limited"),
                    mock_resp,
                ]
                mock_post.side_effect = responses
                result = client._make_request("live/read", {})
                assert mock_post.call_count == 3


def test_no_retry_on_401_auth_error():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_get_auth_headers", return_value={"Authorization": "Basic x", "Timestamp": "1"}):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "unauthorized"
        with patch("requests.Session.post", return_value=mock_resp) as mock_post:
            with pytest.raises(QCAuthenticationError):
                client._make_request("live/read", {})
            assert mock_post.call_count == 1


def test_no_retry_on_400_client_error():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_get_auth_headers", return_value={"Authorization": "Basic x", "Timestamp": "1"}):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "bad request"
        with patch("requests.Session.post", return_value=mock_resp) as mock_post:
            with pytest.raises(QCClientError):
                client._make_request("live/read", {})
            assert mock_post.call_count == 1


def test_json_post_sets_json_content_type_per_request():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_get_auth_headers", return_value={"Authorization": "Basic x", "Timestamp": "1"}):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
            result = client._make_request("live/read", {"projectId": 99999})

    assert result == {"success": True}
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["Content-Type"] == "application/json"
    assert call_kwargs["json"] == {"projectId": 99999}


def test_file_post_allows_requests_to_build_multipart_content_type():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_get_auth_headers", return_value={"Authorization": "Basic x", "Timestamp": "1"}):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True}
        with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
            result = client._make_file_request(
                "object/set",
                data={
                    "organizationId": "org-1",
                    "key": "99999/marketpilot/signals/smoke.json",
                },
                files={"objectData": b'{"paper_trading_only": true}'},
            )

    assert result == {"success": True}
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"] == {"Authorization": "Basic x", "Timestamp": "1"}
    assert "Content-Type" not in call_kwargs["headers"]
    assert call_kwargs["data"] == {
        "organizationId": "org-1",
        "key": "99999/marketpilot/signals/smoke.json",
    }
    assert call_kwargs["files"] == {"objectData": b'{"paper_trading_only": true}'}


def test_retry_on_network_error():
    client = _make_client_with_mocked_auth()
    import requests as req

    call_count = {"n": 0}

    def side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise req.exceptions.ConnectionError("network down")
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"success": True}
        return resp

    with patch.object(client, "_get_auth_headers", return_value={"Authorization": "Basic x", "Timestamp": "1"}):
        with patch("requests.Session.post", side_effect=side_effect) as mock_post:
            result = client._make_request("live/read", {})
            assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# API-04 — Credential Redaction
# ---------------------------------------------------------------------------


def test_credential_redaction_filter_masks_authorization_header():
    f = CredentialRedactionFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Authorization: Basic abc123def456", args=None, exc_info=None,
    )
    f.filter(record)
    assert "abc123def456" not in record.msg
    assert "***REDACTED***" in record.msg


def test_credential_redaction_filter_masks_api_token_env_var():
    f = CredentialRedactionFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="QUANTCONNECT_API_TOKEN=secret123xyz", args=None, exc_info=None,
    )
    f.filter(record)
    assert "secret123xyz" not in record.msg
    assert "***REDACTED***" in record.msg


def test_exception_does_not_leak_credentials():
    token = "SUPER-SECRET-TOKEN-12345"
    err = QCAuthenticationError(
        "Invalid QC credentials — authentication failed",
        status_code=401,
    )
    assert token not in str(err)
    assert token not in repr(err)


# ---------------------------------------------------------------------------
# API-05 — Typed Wrappers
# ---------------------------------------------------------------------------


def test_read_live_algorithm_returns_paper_snapshot():
    from marketpilot.quantconnect_paper import QuantConnectPaperSnapshot

    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("live_read_success.json")
    with patch.object(client, "_make_request", return_value=fixture):
        result = client.read_live_algorithm(project_id=99999, deploy_id="L-00000000000000000000000000000000")
    assert isinstance(result, QuantConnectPaperSnapshot)
    assert len(result.holdings) == 1
    assert result.holdings[0].symbol == "MSFT"
    assert result.holdings[0].quantity == 10


def test_read_live_algorithm_parses_real_live_dashboard_shape():
    from decimal import Decimal

    from marketpilot.quantconnect_paper import QuantConnectDeploymentStatus

    client = _make_client_with_mocked_auth()
    fixture = {
        "success": True,
        "status": "Running",
        "runtimeStatistics": {
            "Equity": "$27,027.03",
            "Unrealized": "$0.00",
        },
        "orders": [],
    }
    with patch.object(client, "_make_request", return_value=fixture):
        result = client.read_live_algorithm(
            project_id=99999,
            deploy_id="L-00000000000000000000000000000000",
        )

    assert result.deployment_status is QuantConnectDeploymentStatus.RUNNING
    assert result.portfolio_equity == Decimal("27027.03")
    assert result.cash == Decimal("0")


def test_read_live_orders_returns_tuple_of_orders():
    from marketpilot.quantconnect_paper import QuantConnectPaperOrder

    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("live_orders_read_success.json")
    with patch.object(client, "_make_request", return_value=fixture):
        result = client.read_live_orders(project_id=99999, deploy_id="L-00000000000000000000000000000000")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(isinstance(o, QuantConnectPaperOrder) for o in result)
    partial = result[0]
    assert partial.quantconnect_order_id == "1001"
    assert partial.symbol == "MSFT"
    assert partial.status == "partiallyfilled"
    assert partial.raw_status == "PartiallyFilled"
    assert partial.quantity == 10
    assert partial.filled_quantity == 4
    assert partial.remaining_quantity == 6
    assert partial.average_fill_price == "420.25"
    assert partial.tag == "mp:sig-001:idem-001"
    assert partial.signal_id == "sig-001"
    assert partial.idempotency_key == "idem-001"
    assert partial.rejection_reason is None
    assert partial.raw_payload["status"] == "PartiallyFilled"

    rejected = result[1]
    assert rejected.quantconnect_order_id == "1002"
    assert rejected.raw_status == "Invalid"
    assert rejected.rejection_reason == "insufficient buying power"
    assert rejected.filled_quantity == 0
    assert rejected.remaining_quantity == 5


def test_read_live_logs_uses_algorithm_id_payload():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_make_request", return_value={"success": True, "LiveLogs": []}) as mock_request:
        result = client.read_live_logs(
            project_id=99999,
            deploy_id="L-paper",
            start_line=5,
            end_line=15,
            deployment_logs=True,
        )

    assert result == {"success": True, "LiveLogs": []}
    mock_request.assert_called_once_with(
        "live/logs/read",
        {
            "format": "json",
            "projectId": 99999,
            "algorithmId": "L-paper",
            "startLine": 5,
            "endLine": 15,
            "deploymentLogs": True,
        },
    )


def test_project_file_and_compile_wrappers_use_official_payloads():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_make_request", return_value={"success": True, "content": "old"}) as mock_request:
        read = client.read_project_file(project_id=99999, name="main.py")
        updated = client.update_project_file_content(
            project_id=99999,
            name="main.py",
            content="print('probe')",
            code_source_id="test",
        )
        created = client.create_compile(project_id=99999)
        result = client.read_compile(project_id=99999, compile_id="C-1")

    assert read == {"success": True, "content": "old"}
    assert updated is True
    assert created == {"success": True, "content": "old"}
    assert result == {"success": True, "content": "old"}
    assert mock_request.call_args_list[0].args == ("files/read", {"projectId": 99999, "name": "main.py"})
    assert mock_request.call_args_list[1].args == (
        "files/update",
        {
            "projectId": 99999,
            "name": "main.py",
            "content": "print('probe')",
            "codeSourceId": "test",
        },
    )
    assert mock_request.call_args_list[2].args == ("compile/create", {"projectId": 99999})
    assert mock_request.call_args_list[3].args == (
        "compile/read",
        {"projectId": 99999, "compileId": "C-1"},
    )


def test_object_store_wrappers_use_official_payloads_and_namespace():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_make_request", return_value={"success": True, "organizationId": "org-1"}) as mock_request:
        account = client.read_account()
        organization_id = client.discover_organization_id()
        metadata = client.read_object_store_metadata(
            organization_id="org-1",
            key="99999/marketpilot/signals/smoke.json",
        )
        fetched = client.get_object_store_file(
            organization_id="org-1",
            key="99999/marketpilot/signals/smoke.json",
        )
        listed = client.list_object_store_files(
            organization_id="org-1",
            path="99999/marketpilot/signals",
        )
        deleted = client.delete_object_store_file(
            organization_id="org-1",
            project_id=99999,
            key="99999/marketpilot/signals/smoke.json",
        )

    assert account["success"] is True
    assert organization_id == "org-1"
    assert metadata["success"] is True
    assert fetched["success"] is True
    assert listed["success"] is True
    assert deleted is True
    assert mock_request.call_args_list[0].args == ("account/read", {})
    assert mock_request.call_args_list[1].args == ("account/read", {})
    assert mock_request.call_args_list[2].args == (
        "object/properties",
        {"organizationId": "org-1", "key": "99999/marketpilot/signals/smoke.json"},
    )
    assert mock_request.call_args_list[3].args == (
        "object/get",
        {"organizationId": "org-1", "keys": ["99999/marketpilot/signals/smoke.json"]},
    )
    assert mock_request.call_args_list[4].args == (
        "object/list",
        {"organizationId": "org-1", "path": "99999/marketpilot/signals"},
    )
    assert mock_request.call_args_list[5].args == (
        "object/delete",
        {"organizationId": "org-1", "key": "99999/marketpilot/signals/smoke.json"},
    )


def test_object_store_upload_uses_multipart_object_data():
    client = _make_client_with_mocked_auth()
    with patch.object(client, "_make_file_request", return_value={"success": True}) as mock_file:
        result = client.upload_object_store_file(
            organization_id="org-1",
            project_id=99999,
            key="99999/marketpilot/signals/smoke.json",
            content=b'{"paper_trading_only": true}',
        )

    assert result == {"success": True}
    mock_file.assert_called_once_with(
        "object/set",
        data={"organizationId": "org-1", "key": "99999/marketpilot/signals/smoke.json"},
        files={"objectData": b'{"paper_trading_only": true}'},
    )


def test_object_store_write_delete_rejects_non_marketpilot_namespace():
    client = _make_client_with_mocked_auth()
    with pytest.raises(QCSafetyError, match="Object Store writes/deletes"):
        client.upload_object_store_file(
            organization_id="org-1",
            project_id=99999,
            key="99999/other/path.json",
            content=b"{}",
        )
    with pytest.raises(QCSafetyError, match="Object Store writes/deletes"):
        client.delete_object_store_file(
            organization_id="org-1",
            project_id=99999,
            key="88888/marketpilot/signals/smoke.json",
        )


def test_qc_command_smoke_refuses_without_enable_flag(monkeypatch):
    module = _load_qc_command_smoke_module()
    monkeypatch.delenv("MARKETPILOT_QC_COMMAND_SMOKE_ENABLED", raising=False)

    with pytest.raises(SystemExit, match="MARKETPILOT_QC_COMMAND_SMOKE_ENABLED"):
        module.run_smoke(
            command_label="marketpilot_signal",
            dry_run=True,
            polls=1,
            poll_seconds=0,
        )


def test_qc_command_smoke_dry_run_redacts_secret_env(monkeypatch):
    module = _load_qc_command_smoke_module()
    monkeypatch.setenv("MARKETPILOT_QC_COMMAND_SMOKE_ENABLED", "1")
    monkeypatch.setenv("QUANTCONNECT_USER_ID", "507952")
    monkeypatch.setenv("QUANTCONNECT_API_TOKEN", "SECRET-TOKEN-DO-NOT-PRINT")
    monkeypatch.setenv("QC_PROJECT_ID", "32900381")
    monkeypatch.setenv("QC_DEPLOY_ID", "L-paper")

    result = module.run_smoke(
        command_label="marketpilot_signal",
        dry_run=True,
        polls=1,
        poll_seconds=0,
    )

    rendered = json.dumps(result)
    assert result["status"] == "dry_run"
    assert result["command_preview"]["command_type"] == "marketpilot_signal"
    assert result["environment"]["QUANTCONNECT_API_TOKEN"] == "configured_redacted"
    assert "SECRET-TOKEN-DO-NOT-PRINT" not in rendered


def test_qc_command_smoke_builds_typed_probe_payload():
    module = _load_qc_command_smoke_module()

    payload = module.build_command("typed_order_command_probe")

    assert payload["$type"] == "MarketPilotSignalCommand"
    assert payload["command_type"] == "marketpilot_signal"
    assert payload["paper_trading_only"] is True
    assert "parameters" not in payload


def test_qc_dispatch_probe_refuses_without_enable_flag(monkeypatch):
    module = _load_qc_dispatch_probe_module()
    monkeypatch.delenv("MARKETPILOT_QC_DISPATCH_PROBE_ENABLED", raising=False)

    with pytest.raises(SystemExit, match="MARKETPILOT_QC_DISPATCH_PROBE_ENABLED"):
        module.run_probe(
            command_label="generic_echo",
            dry_run=True,
            file_name="main.py",
            restore_original=True,
            deploy=False,
            polls=1,
            poll_seconds=0,
            compile_polls=1,
            compile_poll_seconds=0,
        )


def test_qc_dispatch_probe_dry_run_is_sanitized_and_no_order(monkeypatch):
    module = _load_qc_dispatch_probe_module()
    monkeypatch.setenv("MARKETPILOT_QC_DISPATCH_PROBE_ENABLED", "1")
    monkeypatch.setenv("QUANTCONNECT_USER_ID", "507952")
    monkeypatch.setenv("QUANTCONNECT_API_TOKEN", "SECRET-TOKEN-DO-NOT-PRINT")
    monkeypatch.setenv("QC_PROJECT_ID", "32900381")

    result = module.run_probe(
        command_label="generic_echo",
        dry_run=True,
        file_name="main.py",
        restore_original=True,
        deploy=False,
        polls=1,
        poll_seconds=0,
        compile_polls=1,
        compile_poll_seconds=0,
    )

    rendered = json.dumps(result)
    assert result["status"] == "dry_run"
    assert result["command_preview"]["command_type"] == "marketpilot_dispatch_probe"
    assert "$type" not in result["command_preview"]
    assert result["environment"]["QUANTCONNECT_API_TOKEN"] == "configured_redacted"
    assert "SECRET-TOKEN-DO-NOT-PRINT" not in rendered
    algorithm = module.build_echo_algorithm()
    assert "market_order" not in algorithm
    assert "MARKETPILOT_DISPATCH_PROBE_RECEIVED" in algorithm


def test_qc_dispatch_probe_builds_flat_typed_diagnostic_payload():
    module = _load_qc_dispatch_probe_module()

    payload = module.build_command("flat_typed_echo")

    assert payload["$type"] == "MarketPilotDispatchProbeCommand"
    assert payload["command_type"] == "marketpilot_dispatch_probe"
    assert "parameters" not in payload


def test_qc_object_store_smoke_refuses_without_enable_flag(monkeypatch):
    module = _load_qc_object_store_smoke_module()
    monkeypatch.delenv("MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED", raising=False)

    with pytest.raises(SystemExit, match="MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED"):
        module.run_smoke(
            command_label="object_store_signal_probe",
            dry_run=True,
            diagnose_only=False,
            deploy=False,
            cleanup=True,
            file_name="main.py",
            restore_original=True,
            compile_polls=1,
            compile_poll_seconds=0,
            polls=1,
            poll_seconds=0,
        )


def test_qc_object_store_smoke_dry_run_is_sanitized(monkeypatch):
    module = _load_qc_object_store_smoke_module()
    monkeypatch.setenv("MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED", "1")
    monkeypatch.setenv("QUANTCONNECT_USER_ID", "507952")
    monkeypatch.setenv("QUANTCONNECT_API_TOKEN", "SECRET-TOKEN-DO-NOT-PRINT")
    monkeypatch.setenv("QC_PROJECT_ID", "32900381")

    result = module.run_smoke(
        command_label="object_store_signal_probe",
        dry_run=True,
        diagnose_only=False,
        deploy=False,
        cleanup=True,
        file_name="main.py",
        restore_original=True,
        compile_polls=1,
        compile_poll_seconds=0,
        polls=1,
        poll_seconds=0,
    )

    rendered = json.dumps(result)
    assert result["status"] == "dry_run"
    assert result["object_store_key"].startswith("32900381/marketpilot/signals/")
    assert result["signal_preview"]["command_type"] == "marketpilot_signal"
    assert result["signal_preview"]["paper_trading_only"] is True
    assert result["environment"]["QUANTCONNECT_API_TOKEN"] == "configured_redacted"
    assert "SECRET-TOKEN-DO-NOT-PRINT" not in rendered


def test_qc_object_store_smoke_skips_deploy_when_preflight_fails(monkeypatch):
    module = _load_qc_object_store_smoke_module()

    class FakeClient:
        def __init__(self):
            self.compile_calls = 0
            self.deploy_calls = 0

        def discover_organization_id(self):
            return "org-1"

        def upload_object_store_file(self, **_kwargs):
            return {"success": False, "errors": ["Organization not found"]}

        def read_object_store_metadata(self, **_kwargs):
            return {"success": False, "errors": ["File not found"]}

        def create_compile(self, **_kwargs):
            self.compile_calls += 1
            raise AssertionError("compile should be skipped")

        def create_live_algorithm(self, **_kwargs):
            self.deploy_calls += 1
            raise AssertionError("deploy should be skipped")

    fake = FakeClient()
    monkeypatch.setenv("MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED", "1")
    monkeypatch.setenv("QC_PROJECT_ID", "32900381")
    with patch.object(module, "QCApiClient", return_value=fake):
        result = module.run_smoke(
            command_label="object_store_signal_probe",
            dry_run=False,
            diagnose_only=False,
            deploy=True,
            cleanup=True,
            file_name="main.py",
            restore_original=True,
            compile_polls=1,
            compile_poll_seconds=0,
            polls=1,
            poll_seconds=0,
        )

    assert result["status"] == "blocked_external_object_store_permission_or_paid_tier_required"
    assert result["deploy_skipped"] is True
    assert result["object_store_preflight"]["write_available"] is False
    assert fake.compile_calls == 0
    assert fake.deploy_calls == 0


def test_qc_object_store_smoke_diagnose_only_cleans_created_probe(monkeypatch):
    module = _load_qc_object_store_smoke_module()

    class FakeClient:
        def __init__(self):
            self.deleted = False

        def discover_organization_id(self):
            return "org-1"

        def upload_object_store_file(self, **_kwargs):
            return {"success": True}

        def read_object_store_metadata(self, **_kwargs):
            return {"success": True, "size": 42}

        def delete_object_store_file(self, **_kwargs):
            self.deleted = True
            return True

        def read_project_file(self, **_kwargs):
            raise AssertionError("diagnose-only should not read project files")

    fake = FakeClient()
    monkeypatch.setenv("MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED", "1")
    monkeypatch.setenv("QC_PROJECT_ID", "32900381")
    with patch.object(module, "QCApiClient", return_value=fake):
        result = module.run_smoke(
            command_label="object_store_signal_probe",
            dry_run=False,
            diagnose_only=True,
            deploy=True,
            cleanup=True,
            file_name="main.py",
            restore_original=True,
            compile_polls=1,
            compile_poll_seconds=0,
            polls=1,
            poll_seconds=0,
        )

    assert result["status"] == "object_store_write_available"
    assert result["object_store_preflight"]["object_properties"]["success"] is True
    assert result["cleanup_success"] is True
    assert fake.deleted is True


def test_qc_object_store_smoke_stops_created_deployment_by_default(monkeypatch):
    module = _load_qc_object_store_smoke_module()

    class FakeClient:
        def __init__(self):
            self.stopped = False

        def discover_organization_id(self):
            return "org-1"

        def upload_object_store_file(self, **_kwargs):
            return {"success": True}

        def read_object_store_metadata(self, **_kwargs):
            return {"success": True, "size": 42}

        def read_project_file(self, **_kwargs):
            return {"files": [{"name": "main.py", "content": "old"}]}

        def update_project_file_content(self, **_kwargs):
            return True

        def create_compile(self, **_kwargs):
            return {"success": True, "compileId": "C-1"}

        def read_compile(self, **_kwargs):
            return {"success": True, "state": "BuildSuccess", "logs": []}

        def create_live_algorithm(self, **_kwargs):
            return {"success": True, "deployId": "L-paper"}

        def read_live_logs(self, **_kwargs):
            return {"success": True, "logs": ["MarketPilot Object Store signal received."]}

        def read_live_orders_page(self, **_kwargs):
            return {"success": True, "orders": []}

        def delete_object_store_file(self, **_kwargs):
            return True

        def stop_live_algorithm(self, **_kwargs):
            self.stopped = True
            return True

    fake = FakeClient()
    monkeypatch.setenv("MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED", "1")
    monkeypatch.setenv("QC_PROJECT_ID", "32900381")
    monkeypatch.setenv("QC_NODE_ID", "LN-paper")
    monkeypatch.setenv("QC_VERSION_ID", "17838")
    with patch.object(module, "QCApiClient", return_value=fake):
        result = module.run_smoke(
            command_label="object_store_signal_probe",
            dry_run=False,
            diagnose_only=False,
            deploy=True,
            cleanup=True,
            file_name="main.py",
            restore_original=True,
            compile_polls=1,
            compile_poll_seconds=0,
            polls=1,
            poll_seconds=0,
        )

    assert result["status"] == "object_store_delivery_receipt_or_rejection_observed"
    assert result["stop_attempted"] is True
    assert result["stop_success"] is True
    assert fake.stopped is True


def test_qc_object_store_smoke_keep_running_skips_auto_stop(monkeypatch):
    module = _load_qc_object_store_smoke_module()

    class FakeClient:
        def discover_organization_id(self):
            return "org-1"

        def upload_object_store_file(self, **_kwargs):
            return {"success": True}

        def read_object_store_metadata(self, **_kwargs):
            return {"success": True, "size": 42}

        def read_project_file(self, **_kwargs):
            return {"files": [{"name": "main.py", "content": "old"}]}

        def update_project_file_content(self, **_kwargs):
            return True

        def create_compile(self, **_kwargs):
            return {"success": True, "compileId": "C-1"}

        def read_compile(self, **_kwargs):
            return {"success": True, "state": "BuildSuccess", "logs": []}

        def create_live_algorithm(self, **_kwargs):
            return {"success": True, "deployId": "L-paper"}

        def read_live_logs(self, **_kwargs):
            return {"success": True, "logs": []}

        def read_live_orders_page(self, **_kwargs):
            return {"success": True, "orders": []}

        def delete_object_store_file(self, **_kwargs):
            return True

        def stop_live_algorithm(self, **_kwargs):
            raise AssertionError("stop should be skipped when keep-running is active")

    monkeypatch.setenv("MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED", "1")
    monkeypatch.setenv("QC_PROJECT_ID", "32900381")
    monkeypatch.setenv("QC_NODE_ID", "LN-paper")
    monkeypatch.setenv("QC_VERSION_ID", "17838")
    with patch.object(module, "QCApiClient", return_value=FakeClient()):
        result = module.run_smoke(
            command_label="object_store_signal_probe",
            dry_run=False,
            diagnose_only=False,
            deploy=True,
            cleanup=True,
            file_name="main.py",
            restore_original=True,
            compile_polls=1,
            compile_poll_seconds=0,
            polls=1,
            poll_seconds=0,
            stop_after_deploy=False,
        )

    assert result["status"] == "object_store_written_no_algorithm_receipt_observed"
    assert result["stop_attempted"] is False


def test_create_live_algorithm_hardcodes_paper_brokerage():
    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("live_create_success.json")
    with patch.object(client, "_make_request", return_value=fixture) as mock_req:
        client.create_live_algorithm(
            project_id=99999,
            compile_id="C-1",
            node_id="N-1",
            version_id="-1",
            data_providers={"QuantConnectBrokerage": {"id": "QuantConnectBrokerage"}},
        )
    call_args = mock_req.call_args
    payload = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("payload")
    assert call_args[0][0] == "live/create"
    assert payload["projectId"] == 99999
    assert payload["compileId"] == "C-1"
    assert payload["nodeId"] == "N-1"
    assert payload["versionId"] == "-1"
    assert payload["brokerage"]["id"] == "QuantConnectBrokerage"
    assert payload["brokerage"]["environment"] == "live-paper"
    assert "InteractiveBrokersBrokerage" not in json.dumps(payload)
    assert payload["dataProviders"] == {
        "QuantConnectBrokerage": {"id": "QuantConnectBrokerage"}
    }


def test_create_live_command_payload():
    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("live_command_success.json")
    command = {
        "command_type": "marketpilot_signal",
        "signal_id": "sig-001",
        "idempotency_key": "idem-001",
        "symbol": "MSFT",
        "quantity": 10,
    }
    with patch.object(client, "_make_request", return_value=fixture) as mock_req:
        delivered = client.create_live_command(project_id=99999, command=command)

    assert delivered is True
    call_args = mock_req.call_args
    assert call_args[0][0] == "live/commands/create"
    payload = call_args[0][1]
    assert payload == {"projectId": 99999, "command": command}
    assert "symbol" not in payload
    assert "quantity" not in payload
    assert "order_type" not in payload


def test_read_live_orders_page_uses_official_endpoint():
    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("live_orders_read_success.json")
    with patch.object(client, "_make_request", return_value=fixture) as mock_req:
        result = client.read_live_orders_page(
            project_id=99999,
            deploy_id="L-00000000000000000000000000000000",
            start=0,
            end=100,
        )

    assert result == fixture
    call_args = mock_req.call_args
    assert call_args[0][0] == "live/orders/read"
    assert call_args[0][1] == {
        "projectId": 99999,
        "algorithmId": "L-00000000000000000000000000000000",
        "start": 0,
        "end": 100,
    }


def test_create_backtest_returns_response_with_backtest_id():
    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("backtests_read_success.json")
    with patch.object(client, "_make_request", return_value=fixture):
        result = client.create_backtest(project_id=99999, compile_id="C-1", backtest_name="Test")
    assert "backtest" in result


# ---------------------------------------------------------------------------
# SAFE-01 — PAPER_TRADING_ONLY Assertion
# ---------------------------------------------------------------------------


def test_paper_trading_only_constant_is_true():
    from marketpilot.constants import PAPER_TRADING_ONLY

    assert PAPER_TRADING_ONLY is True


# ---------------------------------------------------------------------------
# SAFE-02 — No Live Brokerage Paths (Meta-Tests)
# ---------------------------------------------------------------------------


def test_no_direct_quantconnect_urls_outside_qc_api():
    """Ensure no module besides qc_api.py makes direct requests to QC URLs."""
    import re

    marketpilot_dir = Path(__file__).parent.parent / "marketpilot"
    pattern = re.compile(r"quantconnect\.com/api", re.IGNORECASE)
    violations = []
    for py_file in marketpilot_dir.rglob("*.py"):
        if py_file.name == "qc_api.py":
            continue
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if pattern.search(content):
            violations.append(str(py_file.relative_to(marketpilot_dir.parent)))
    assert not violations, f"Direct QC URL usage found in: {violations}"


def test_no_live_brokerage_credential_attributes():
    """Ensure QCApiClient has no attribute for live/real brokerage creds."""
    forbidden = {"live_brokerage", "real_broker", "brokerage_credentials", "live_credentials"}
    attrs = set(dir(QCApiClient))
    found = attrs & forbidden
    assert not found, f"Forbidden attributes found: {found}"
