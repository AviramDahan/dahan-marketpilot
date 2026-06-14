"""Single-password dashboard authentication helpers."""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from enum import Enum

from .config import DashboardConfig
from .redaction import redact_text


class AuthStatus(str, Enum):
    AUTH_REQUIRED = "auth_required"
    AUTH_FAILED = "auth_failed"
    AUTHENTICATED = "authenticated"


@dataclass(frozen=True)
class DashboardAuth:
    status: AuthStatus
    authenticated: bool
    message: str = ""

    @classmethod
    def from_config(cls, config: DashboardConfig) -> "DashboardAuth":
        if not config.password:
            return cls(
                status=AuthStatus.AUTH_REQUIRED,
                authenticated=False,
                message="Dashboard password is not configured.",
            )
        return cls(status=AuthStatus.AUTH_REQUIRED, authenticated=False, message="Authentication required.")

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "authenticated": self.authenticated,
            "message": redact_text(self.message),
        }


def authenticate_dashboard(config: DashboardConfig, candidate_password: str | None) -> DashboardAuth:
    if not config.password:
        return DashboardAuth.from_config(config)

    candidate = str(candidate_password or "")
    if hmac.compare_digest(candidate, config.password):
        return DashboardAuth(
            status=AuthStatus.AUTHENTICATED,
            authenticated=True,
            message="Authenticated.",
        )
    return DashboardAuth(
        status=AuthStatus.AUTH_FAILED,
        authenticated=False,
        message="Authentication failed.",
    )


def dashboard_data_visible(auth: DashboardAuth) -> bool:
    return auth.authenticated and auth.status is AuthStatus.AUTHENTICATED
