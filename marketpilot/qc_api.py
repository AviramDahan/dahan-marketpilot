"""QuantConnect Cloud REST API client with defense-in-depth safety."""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from time import time
from typing import Any, Mapping

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperFill,
    QuantConnectPaperOrder,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)

# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------


class QCApiError(Exception):
    """Base exception for all QC API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class QCAuthenticationError(QCApiError):
    """401 — invalid credentials; not retryable."""


class QCRateLimitError(QCApiError):
    """429 — rate limited; retryable."""


class QCServerError(QCApiError):
    """5xx — server error; retryable."""


class QCClientError(QCApiError):
    """4xx (not 401/429) — client error; not retryable."""


class QCNetworkError(QCApiError):
    """Connection/timeout error; retryable."""


class QCSafetyError(QCApiError):
    """Local safety gate violation; request never sent."""


# ---------------------------------------------------------------------------
# Credential redaction logging filter
# ---------------------------------------------------------------------------


class CredentialRedactionFilter(logging.Filter):
    """Scrubs credential patterns from log records before output."""

    _PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"Authorization:\s*Basic\s+\S+", re.IGNORECASE),
        re.compile(r"QUANTCONNECT_API_TOKEN[=:]\s*\S+", re.IGNORECASE),
        re.compile(r"api_token[=:]\s*['\"]?\S+", re.IGNORECASE),
    )

    _REPLACEMENT = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pat in self._PATTERNS:
                record.msg = pat.sub(self._REPLACEMENT, record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: pat.sub(self._REPLACEMENT, v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                    for pat in self._PATTERNS
                }
            elif isinstance(record.args, tuple):
                new_args: list[object] = []
                for arg in record.args:
                    if isinstance(arg, str):
                        for pat in self._PATTERNS:
                            arg = pat.sub(self._REPLACEMENT, arg)
                    new_args.append(arg)
                record.args = tuple(new_args)
        return True


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QCApiConfig:
    """Immutable configuration for QC API client."""

    user_id: str
    api_token: str
    base_url: str = "https://www.quantconnect.com/api/v2"


# ---------------------------------------------------------------------------
# Endpoint allowlist (safety gate)
# ---------------------------------------------------------------------------

_ALLOWED_ENDPOINTS: frozenset[str] = frozenset(
    {
        "authenticate",
        "live/read",
        "live/list",
        "live/logs/read",
        "backtests/create",
        "backtests/read",
        "backtests/list",
        "compile/create",
        "compile/read",
        "files/read",
        "files/update",
        "projects/read",
    }
)

_PAPER_GATED_ENDPOINTS: frozenset[str] = frozenset(
    {
        "live/create",
        "live/commands/create",
        "live/orders/read",
        "live/update/stop",
        "live/update/liquidate",
    }
)

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

_logger = logging.getLogger("marketpilot.qc_api")
_logger.addFilter(CredentialRedactionFilter())


# ---------------------------------------------------------------------------
# QCApiClient
# ---------------------------------------------------------------------------


class QCApiClient:
    """Authenticated, safety-gated client for QuantConnect Cloud REST API v2."""

    def __init__(self, config: QCApiConfig | None = None) -> None:
        if config is None:
            user_id = os.environ.get("QUANTCONNECT_USER_ID", "").strip()
            api_token = os.environ.get("QUANTCONNECT_API_TOKEN", "").strip()
            if not user_id or not api_token:
                raise QCAuthenticationError(
                    "QUANTCONNECT_USER_ID and QUANTCONNECT_API_TOKEN environment "
                    "variables are required but missing or empty."
                )
            config = QCApiConfig(user_id=user_id, api_token=api_token)

        self._config = config
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})
        _logger.addFilter(CredentialRedactionFilter())
        self._validate_credentials()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _get_auth_headers(self) -> dict[str, str]:
        """Generate fresh HMAC-SHA256 authentication headers (never cached)."""
        timestamp = str(int(time()))
        token_bytes = f"{self._config.api_token}:{timestamp}".encode("utf-8")
        hashed = hashlib.sha256(token_bytes).hexdigest()
        credentials = f"{self._config.user_id}:{hashed}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {encoded}", "Timestamp": timestamp}

    def _validate_credentials(self) -> None:
        """Fail-fast credential check via GET /authenticate."""
        url = f"{self._config.base_url}/authenticate"
        headers = self._get_auth_headers()
        try:
            resp = self._session.get(url, headers=headers, timeout=15)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            raise QCNetworkError(
                "Network error during credential validation"
            ) from exc

        if resp.status_code == 401:
            raise QCAuthenticationError(
                "Invalid QC credentials — authentication failed",
                status_code=401,
                response_body=resp.text,
            )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise QCAuthenticationError(
                "Invalid QC credentials — authentication failed",
                response_body=resp.text,
            )

    # ------------------------------------------------------------------
    # Safety gate
    # ------------------------------------------------------------------

    def _validate_endpoint(self, endpoint: str) -> None:
        """Refuse requests to endpoints outside the safety allowlist."""
        all_allowed = _ALLOWED_ENDPOINTS | _PAPER_GATED_ENDPOINTS
        if endpoint not in all_allowed:
            raise QCSafetyError(
                f"Endpoint '{endpoint}' is not in the safety allowlist"
            )
        if endpoint in _PAPER_GATED_ENDPOINTS:
            if not PAPER_TRADING_ONLY:
                raise QCSafetyError(
                    "PAPER_TRADING_ONLY must be True for deployment endpoints"
                )

    # ------------------------------------------------------------------
    # Core request (with retry)
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(
            (QCRateLimitError, QCServerError, QCNetworkError)
        ),
        wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _make_request(self, endpoint: str, payload: dict | None = None) -> dict:
        """Execute an authenticated, safety-gated request to the QC API."""
        self._validate_endpoint(endpoint)

        method = "GET" if endpoint == "authenticate" else "POST"
        url = f"{self._config.base_url}/{endpoint}"
        headers = self._get_auth_headers()

        try:
            if method == "GET":
                resp = self._session.get(url, headers=headers, timeout=30)
            else:
                resp = self._session.post(
                    url, headers=headers, json=payload or {}, timeout=30
                )
        except requests.exceptions.Timeout as exc:
            raise QCNetworkError(
                f"Timeout calling {endpoint}", status_code=None
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise QCNetworkError(
                f"Connection error calling {endpoint}", status_code=None
            ) from exc

        status = resp.status_code
        if status == 401:
            raise QCAuthenticationError(
                "Authentication failed",
                status_code=status,
                response_body=resp.text,
            )
        if status == 429:
            raise QCRateLimitError(
                "Rate limited by QC API",
                status_code=status,
                response_body=resp.text,
            )
        if 500 <= status < 600:
            raise QCServerError(
                f"QC server error ({status})",
                status_code=status,
                response_body=resp.text,
            )
        if 400 <= status < 500:
            raise QCClientError(
                f"QC client error ({status})",
                status_code=status,
                response_body=resp.text,
            )

        return resp.json()

    # ------------------------------------------------------------------
    # Paper-gated endpoint wrappers
    # ------------------------------------------------------------------

    def create_live_algorithm(
        self,
        *,
        project_id: int,
        compile_id: str,
        node_id: str,
        version_id: str,
        data_providers: Mapping[str, Mapping[str, object]],
    ) -> dict:
        """Deploy a live paper trading algorithm (paper brokerage hardcoded)."""
        providers = _validate_paper_data_providers(data_providers)
        payload = {
            "versionId": version_id,
            "projectId": project_id,
            "compileId": compile_id,
            "nodeId": node_id,
            "brokerage": {
                "id": "QuantConnectBrokerage",
                "environment": "live-paper",
            },
            "dataProviders": providers,
        }
        return self._make_request("live/create", payload)

    def create_live_command(
        self, *, project_id: int, command: Mapping[str, object]
    ) -> bool:
        """Deliver a command to a running paper algorithm.

        A successful response only means QuantConnect accepted command delivery.
        Order and fill status must be read from QuantConnect live orders.
        """
        payload = {"projectId": project_id, "command": dict(command)}
        response = self._make_request("live/commands/create", payload)
        return bool(response.get("success", False))

    def stop_live_algorithm(self, *, project_id: int) -> bool:
        """Stop a running live algorithm."""
        response = self._make_request("live/update/stop", {"projectId": project_id})
        return response.get("success", False)

    def liquidate_live_algorithm(self, *, project_id: int) -> bool:
        """Liquidate all positions in a live algorithm."""
        response = self._make_request(
            "live/update/liquidate", {"projectId": project_id}
        )
        return response.get("success", False)

    # ------------------------------------------------------------------
    # Read-only endpoint wrappers
    # ------------------------------------------------------------------

    def read_live_algorithm(
        self, *, project_id: int, deploy_id: str
    ) -> QuantConnectPaperSnapshot:
        """Read live algorithm state and return a typed snapshot."""
        response = self._make_request(
            "live/read", {"projectId": project_id, "deployId": deploy_id}
        )

        # Parse holdings
        raw_holdings = response.get("holdings", {})
        holdings: list[QuantConnectHolding] = []
        for _symbol, h in raw_holdings.items():
            if isinstance(h, dict) and h.get("quantity", 0) != 0:
                holdings.append(
                    QuantConnectHolding(
                        symbol=h.get("symbol", {}).get("value", _symbol),
                        quantity=int(h.get("quantity", 0)),
                        average_price=Decimal(str(h.get("averagePrice", 0))),
                        market_price=Decimal(str(h.get("marketPrice", 0))),
                    )
                )

        # Parse orders
        raw_orders = response.get("orders", {})
        orders: list[QuantConnectPaperOrder] = []
        for _oid, o in raw_orders.items() if isinstance(raw_orders, dict) else enumerate(raw_orders):
            if isinstance(o, dict):
                orders.append(
                    QuantConnectPaperOrder(
                        quantconnect_order_id=str(o.get("id", _oid)),
                        symbol=o.get("symbol", {}).get("value", "UNKNOWN"),
                        status=o.get("status", "unknown"),
                        quantity=int(o.get("quantity", 0)),
                        submitted_at=datetime.fromisoformat(
                            o["createdTime"]
                        ) if "createdTime" in o else datetime.now(timezone.utc),
                    )
                )

        # Parse fills (from order events)
        fills: list[QuantConnectPaperFill] = []
        for _oid, o in raw_orders.items() if isinstance(raw_orders, dict) else enumerate(raw_orders):
            if isinstance(o, dict) and o.get("status", "").lower() == "filled":
                fills.append(
                    QuantConnectPaperFill(
                        quantconnect_order_id=str(o.get("id", _oid)),
                        symbol=o.get("symbol", {}).get("value", "UNKNOWN"),
                        quantity=int(o.get("quantity", 0)),
                        fill_price=Decimal(str(o.get("price", 0))),
                        filled_at=datetime.fromisoformat(
                            o["lastFillTime"]
                        ) if "lastFillTime" in o else datetime.now(timezone.utc),
                    )
                )

        # Parse cash and equity. QuantConnect live/read can return either the
        # internal API shape (`cash`, `statistics`) or the live-dashboard shape
        # (`runtimeStatistics` with formatted currency strings).
        cash = _decimal_from_quantconnect_value(
            response.get("cash", {}).get("USD", {}).get("amount", 0)
            if isinstance(response.get("cash"), dict)
            else response.get("cash", 0)
        )
        statistics = response.get("statistics", {})
        runtime_statistics = response.get("runtimeStatistics", {})
        portfolio_equity = _decimal_from_quantconnect_value(
            statistics.get("Equity", runtime_statistics.get("Equity", cash))
        )
        unrealized_profit = _decimal_from_quantconnect_value(
            statistics.get("Unrealized", runtime_statistics.get("Unrealized", 0))
        )

        # Deployment and algorithm status
        state = str(response.get("state") or response.get("status") or "").lower()
        try:
            deployment_status = QuantConnectDeploymentStatus(state)
        except ValueError:
            deployment_status = QuantConnectDeploymentStatus.NOT_RUN

        try:
            algorithm_status = QuantConnectAlgorithmStatus(state)
        except ValueError:
            algorithm_status = QuantConnectAlgorithmStatus.NOT_RUN

        return QuantConnectPaperSnapshot(
            fixture_label=deploy_id,
            captured_at=datetime.now(timezone.utc),
            cash=cash,
            portfolio_equity=portfolio_equity,
            holdings=tuple(holdings),
            orders=tuple(orders),
            fills=tuple(fills),
            deployment_status=deployment_status,
            algorithm_status=algorithm_status,
            performance=QuantConnectPaperPerformance(
                total_orders=len(orders),
                total_fills=len(fills),
                unrealized_profit=unrealized_profit,
            ),
        )

    def read_live_orders(
        self, *, project_id: int, deploy_id: str
    ) -> tuple[QuantConnectPaperOrder, ...]:
        """Read live orders and return typed order objects."""
        response = self.read_live_orders_page(
            project_id=project_id,
            deploy_id=deploy_id,
            start=0,
            end=100,
        )
        raw_orders = response.get("orders", {})
        orders: list[QuantConnectPaperOrder] = []
        for _oid, o in raw_orders.items() if isinstance(raw_orders, dict) else enumerate(raw_orders):
            if isinstance(o, dict):
                orders.append(_parse_live_order(_oid, o))
        return tuple(orders)

    def read_live_orders_page(
        self,
        *,
        project_id: int,
        deploy_id: str,
        start: int = 0,
        end: int = 100,
    ) -> dict:
        """Read one official QuantConnect live orders page."""
        return self._make_request(
            "live/orders/read",
            {
                "projectId": project_id,
                "algorithmId": deploy_id,
                "start": start,
                "end": end,
            },
        )

    def read_live_logs(
        self,
        *,
        project_id: int,
        deploy_id: str,
        start: int = 0,
        end: int = 100,
    ) -> dict:
        """Read QuantConnect live logs for a running paper algorithm."""
        return self._make_request(
            "live/logs/read",
            {
                "projectId": project_id,
                "algorithmId": deploy_id,
                "start": start,
                "end": end,
            },
        )

    def read_project_file(self, *, project_id: int, name: str) -> dict:
        """Read a single QuantConnect project file."""
        return self._make_request(
            "files/read",
            {
                "projectId": project_id,
                "name": name,
            },
        )

    def update_project_file_content(
        self,
        *,
        project_id: int,
        name: str,
        content: str,
        code_source_id: str = "Dahan MarketPilot Codex",
    ) -> bool:
        """Update one QuantConnect project file through the official API."""
        response = self._make_request(
            "files/update",
            {
                "projectId": project_id,
                "name": name,
                "content": content,
                "codeSourceId": code_source_id,
            },
        )
        return bool(response.get("success", False))

    def create_compile(self, *, project_id: int) -> dict:
        """Create a QuantConnect cloud compile job."""
        return self._make_request("compile/create", {"projectId": project_id})

    def read_compile(self, *, project_id: int, compile_id: str) -> dict:
        """Read a QuantConnect cloud compile result."""
        return self._make_request(
            "compile/read",
            {
                "projectId": project_id,
                "compileId": compile_id,
            },
        )

    def create_backtest(
        self, *, project_id: int, compile_id: str, backtest_name: str
    ) -> dict:
        """Create a new backtest run."""
        payload = {
            "projectId": project_id,
            "compileId": compile_id,
            "backtestName": backtest_name,
        }
        return self._make_request("backtests/create", payload)

    def read_backtest(self, *, project_id: int, backtest_id: str) -> dict:
        """Read backtest results."""
        return self._make_request(
            "backtests/read",
            {"projectId": project_id, "backtestId": backtest_id},
        )


def _validate_paper_data_providers(
    data_providers: Mapping[str, Mapping[str, object]]
) -> dict[str, dict[str, object]]:
    """Allow only id-only QuantConnect paper data provider configuration."""
    if not data_providers:
        raise QCSafetyError("dataProviders must be explicit for live paper deployment")

    normalized: dict[str, dict[str, object]] = {}
    for name, config in data_providers.items():
        provider_name = str(name).strip()
        provider_id = str(config.get("id", "")).strip() if isinstance(config, Mapping) else ""
        if provider_name != "QuantConnectBrokerage" or provider_id != "QuantConnectBrokerage":
            raise QCSafetyError(
                "Only QuantConnectBrokerage data provider is allowed for paper deployment"
            )
        extra_keys = set(config) - {"id"}
        if extra_keys:
            raise QCSafetyError(
                "Data provider credentials or account settings are not allowed in paper deployment payloads"
            )
        normalized[provider_name] = {"id": provider_id}
    return normalized


def _decimal_from_quantconnect_value(value: object) -> Decimal:
    """Parse numeric QuantConnect values, including formatted dashboard strings."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float):
        return Decimal(str(value))
    text = str(value).strip()
    if not text:
        return Decimal("0")
    normalized = text.replace("$", "").replace(",", "").replace("%", "").strip()
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = f"-{normalized[1:-1]}"
    if not normalized:
        return Decimal("0")
    return Decimal(normalized)


def _parse_live_order(order_key: object, payload: Mapping[str, Any]) -> QuantConnectPaperOrder:
    tag = _first_string(payload, "tag", "Tag", "orderTag", "OrderTag")
    signal_id, idempotency_key = _parse_marketpilot_order_tag(tag)
    quantity = _to_int(payload.get("quantity", payload.get("Quantity", 0)))
    filled_quantity = _to_int(
        payload.get(
            "quantityFilled",
            payload.get("filledQuantity", payload.get("fillQuantity", payload.get("QuantityFilled", 0))),
        )
    )
    remaining_quantity = _to_int(
        payload.get(
            "remainingQuantity",
            payload.get("quantityRemaining", max(quantity - filled_quantity, 0)),
        )
    )
    raw_status = str(payload.get("status", payload.get("Status", "unknown")))
    return QuantConnectPaperOrder(
        quantconnect_order_id=str(payload.get("id", payload.get("orderId", order_key))),
        symbol=_extract_symbol(payload.get("symbol", payload.get("Symbol"))),
        status=raw_status,
        quantity=quantity,
        submitted_at=_parse_qc_datetime(
            _first_string(payload, "createdTime", "CreatedTime", "time", "Time")
        ),
        idempotency_key=idempotency_key,
        signal_id=signal_id,
        raw_status=raw_status,
        filled_quantity=filled_quantity,
        remaining_quantity=remaining_quantity,
        average_fill_price=_first_string(
            payload, "averageFillPrice", "AverageFillPrice", "fillPrice", "price"
        ),
        tag=tag,
        rejection_reason=_first_string(
            payload, "message", "Message", "rejectionReason", "RejectionReason"
        ),
        raw_payload=dict(payload),
    )


def _parse_marketpilot_order_tag(tag: str | None) -> tuple[str | None, str | None]:
    if not tag:
        return None, None
    parts = tag.split(":", 2)
    if len(parts) == 3 and parts[0] == "mp":
        return parts[1] or None, parts[2] or None
    return None, None


def _extract_symbol(value: object) -> str:
    if isinstance(value, Mapping):
        return str(value.get("value", value.get("Value", "UNKNOWN")))
    if value is None:
        return "UNKNOWN"
    return str(value)


def _first_string(payload: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return str(value)
    return None


def _to_int(value: object) -> int:
    if value is None or value == "":
        return 0
    return int(Decimal(str(value)))


def _parse_qc_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
