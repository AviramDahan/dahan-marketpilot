"""QuantConnect Cloud Paper Trading prerequisite and operator-command contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


QUANTCONNECT_PAPER_BROKERAGE = "QuantConnect Paper Trading"


class QuantConnectPaperStatusCode(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    CONFIGURED_OPERATOR_ACTION_REQUIRED = "configured_operator_action_required"


class QuantConnectDeploymentStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class QuantConnectAlgorithmStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    RUNNING = "running"
    STOPPED = "stopped"
    RUNTIME_ERROR = "runtime_error"


@dataclass(frozen=True)
class QuantConnectHolding:
    symbol: str
    quantity: int
    average_price: Decimal
    market_price: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class QuantConnectPaperOrder:
    quantconnect_order_id: str
    symbol: str
    status: str
    quantity: int
    submitted_at: datetime
    idempotency_key: str | None = None
    order_role: str = "entry"

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantconnect_order_id", self.quantconnect_order_id.strip())
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "status", self.status.strip().lower())
        object.__setattr__(self, "order_role", self.order_role.strip().lower())
        if not self.quantconnect_order_id:
            raise ValueError("quantconnect_order_id is required after QuantConnect submission.")


@dataclass(frozen=True)
class QuantConnectPaperFill:
    quantconnect_order_id: str
    symbol: str
    quantity: int
    fill_price: Decimal
    filled_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantconnect_order_id", self.quantconnect_order_id.strip())
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        if not self.quantconnect_order_id:
            raise ValueError("quantconnect_order_id is required for QuantConnect fills.")


@dataclass(frozen=True)
class QuantConnectPaperPerformance:
    total_orders: int
    total_fills: int
    unrealized_profit: Decimal


@dataclass(frozen=True)
class QuantConnectPaperSnapshot:
    fixture_label: str
    captured_at: datetime
    cash: Decimal
    portfolio_equity: Decimal
    holdings: tuple[QuantConnectHolding, ...]
    orders: tuple[QuantConnectPaperOrder, ...]
    fills: tuple[QuantConnectPaperFill, ...]
    deployment_status: QuantConnectDeploymentStatus
    algorithm_status: QuantConnectAlgorithmStatus
    performance: QuantConnectPaperPerformance
    authoritative_source: str = "quantconnect"

    def __post_init__(self) -> None:
        if self.authoritative_source != "quantconnect":
            raise ValueError("QuantConnect Paper snapshots must use quantconnect as authoritative_source.")
        if not self.fixture_label.strip():
            raise ValueError("fixture_label is required; use deterministic-test-fixture for offline tests.")
        if self.fixture_label == "deterministic-test-fixture" and self.captured_at.tzinfo is None:
            raise ValueError("deterministic test fixtures must include timezone-aware captured_at timestamps.")


@dataclass(frozen=True)
class QuantConnectPaperPrerequisites:
    quantconnect_account: bool = False
    organization_access: bool = False
    paper_live_node: bool = False
    project_id: bool = False
    api_credentials: bool = False
    data_provider: bool = False
    brokerage_target: str = QUANTCONNECT_PAPER_BROKERAGE

    @property
    def missing(self) -> tuple[str, ...]:
        missing = []
        if not self.quantconnect_account:
            missing.append("quantconnect_account")
        if not self.organization_access:
            missing.append("organization_access")
        if not self.paper_live_node:
            missing.append("paper_live_node")
        if not self.project_id:
            missing.append("project_id")
        if not self.api_credentials:
            missing.append("api_credentials")
        if not self.data_provider:
            missing.append("data_provider")
        return tuple(missing)


@dataclass(frozen=True)
class QuantConnectPaperStatus:
    status_code: QuantConnectPaperStatusCode
    allowed_brokerage_target: str
    missing_prerequisites: tuple[str, ...] = field(default_factory=tuple)
    reasons: tuple[str, ...] = field(default_factory=tuple)
    command_text: str | None = None
    executed: bool = False
    deployment_id: str | None = None


def validate_quantconnect_paper_brokerage(target: str) -> str:
    normalized = target.strip()
    if normalized != QUANTCONNECT_PAPER_BROKERAGE:
        raise ValueError("Only QuantConnect Paper Trading is allowed as a brokerage target.")
    return QUANTCONNECT_PAPER_BROKERAGE


def evaluate_quantconnect_paper_status(
    prerequisites: QuantConnectPaperPrerequisites,
) -> QuantConnectPaperStatus:
    validate_quantconnect_paper_brokerage(prerequisites.brokerage_target)
    missing = prerequisites.missing
    if missing:
        return QuantConnectPaperStatus(
            status_code=QuantConnectPaperStatusCode.NOT_CONFIGURED,
            allowed_brokerage_target=QUANTCONNECT_PAPER_BROKERAGE,
            missing_prerequisites=missing,
            reasons=("missing_quantconnect_prerequisites",),
        )
    return QuantConnectPaperStatus(
        status_code=QuantConnectPaperStatusCode.NOT_RUN,
        allowed_brokerage_target=QUANTCONNECT_PAPER_BROKERAGE,
        reasons=("operator_deployment_not_run",),
    )


def render_operator_deployment_command(
    prerequisites: QuantConnectPaperPrerequisites,
    *,
    project_id_env_var: str = "QUANTCONNECT_PROJECT_ID",
) -> QuantConnectPaperStatus:
    base_status = evaluate_quantconnect_paper_status(prerequisites)
    if base_status.status_code is QuantConnectPaperStatusCode.NOT_CONFIGURED:
        return base_status

    project_ref = _env_reference(project_id_env_var)
    return QuantConnectPaperStatus(
        status_code=QuantConnectPaperStatusCode.CONFIGURED_OPERATOR_ACTION_REQUIRED,
        allowed_brokerage_target=QUANTCONNECT_PAPER_BROKERAGE,
        reasons=("operator_must_run_quantconnect_cloud_paper_deployment",),
        command_text=f'lean cloud live deploy "{project_ref}" --push',
        executed=False,
        deployment_id=None,
    )


def _env_reference(name: str) -> str:
    normalized = name.strip().upper()
    if not normalized or any(char.isspace() for char in normalized):
        raise ValueError("environment variable name must be non-empty and contain no whitespace.")
    return f"${normalized}"
