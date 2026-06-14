"""QuantConnect Cloud Paper Trading prerequisite and operator-command contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


QUANTCONNECT_PAPER_BROKERAGE = "QuantConnect Paper Trading"


class QuantConnectPaperStatusCode(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    CONFIGURED_OPERATOR_ACTION_REQUIRED = "configured_operator_action_required"


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
