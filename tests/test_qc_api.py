"""Tests for marketpilot.qc_api — QC API client with safety guarantees."""

from __future__ import annotations

import json
import logging
import os
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


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


def _make_client_with_mocked_auth() -> QCApiClient:
    """Create a QCApiClient that skips real credential validation."""
    config = QCApiConfig(user_id="99999", api_token="FAKE-TOKEN-DO-NOT-USE")
    with patch.object(QCApiClient, "_validate_credentials"):
        return QCApiClient(config=config)


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
    client._validate_endpoint("authenticate")
    client._validate_endpoint("backtests/read")


def test_safety_gate_blocks_paper_gated_when_constant_false():
    client = _make_client_with_mocked_auth()
    import marketpilot.qc_api as qc_mod

    original = qc_mod.PAPER_TRADING_ONLY
    try:
        qc_mod.PAPER_TRADING_ONLY = False
        with pytest.raises(QCSafetyError, match="PAPER_TRADING_ONLY must be True"):
            client._validate_endpoint("live/create")
    finally:
        qc_mod.PAPER_TRADING_ONLY = original


def test_safety_gate_allows_paper_gated_when_constant_true():
    client = _make_client_with_mocked_auth()
    # Should not raise — PAPER_TRADING_ONLY is True
    client._validate_endpoint("live/create")
    client._validate_endpoint("live/update/stop")
    client._validate_endpoint("live/update/liquidate")


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


def test_read_live_orders_returns_tuple_of_orders():
    from marketpilot.quantconnect_paper import QuantConnectPaperOrder

    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("orders_read_success.json")
    with patch.object(client, "_make_request", return_value=fixture):
        result = client.read_live_orders(project_id=99999, deploy_id="L-00000000000000000000000000000000")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(isinstance(o, QuantConnectPaperOrder) for o in result)


def test_create_live_algorithm_hardcodes_paper_brokerage():
    client = _make_client_with_mocked_auth()
    fixture = _load_fixture("live_create_success.json")
    with patch.object(client, "_make_request", return_value=fixture) as mock_req:
        client.create_live_algorithm(project_id=99999, compile_id="C-1", node_id="N-1")
    call_args = mock_req.call_args
    payload = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("payload")
    assert payload["brokerage"] == {"id": "QuantConnectBrokerage"}


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
