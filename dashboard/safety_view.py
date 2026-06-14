"""Pure helpers for rendering the read-only dashboard shell."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.auth import AuthStatus, DashboardAuth, dashboard_data_visible
from dashboard.config import DashboardConfig, DEFAULT_ALLOWED_ACTIONS, DEFAULT_NAVIGATION_SECTIONS
from dashboard.models import DashboardSafetyState, default_safety_state


READ_ONLY_ALLOWED_ACTIONS = DEFAULT_ALLOWED_ACTIONS
DASHBOARD_NAVIGATION_SECTIONS = DEFAULT_NAVIGATION_SECTIONS


@dataclass(frozen=True)
class DashboardShellView:
    title: str
    disclaimer: str
    paper_only_status: str
    read_only_status: str
    status: str
    sections: tuple[str, ...]
    controls: tuple[str, ...]
    data_visible: bool


def safety_lines(state: DashboardSafetyState | None = None) -> list[str]:
    current = state or default_safety_state()
    return [
        current.title,
        current.disclaimer,
        current.paper_only_status,
        current.read_only_status,
        current.data_status,
        current.scope_note,
    ]


def render_markdown(state: DashboardSafetyState | None = None) -> str:
    return "\n\n".join(safety_lines(state))


def build_dashboard_shell(config: DashboardConfig, auth: DashboardAuth) -> DashboardShellView:
    state = default_safety_state()
    visible = dashboard_data_visible(auth)
    if not visible:
        return DashboardShellView(
            title=state.title,
            disclaimer=state.disclaimer,
            paper_only_status=state.paper_only_status,
            read_only_status=state.read_only_status,
            status=auth.status.value,
            sections=(),
            controls=("login",),
            data_visible=False,
        )

    return DashboardShellView(
        title=state.title,
        disclaimer=state.disclaimer,
        paper_only_status=state.paper_only_status,
        read_only_status=state.read_only_status,
        status="Source and freshness metadata visible on every dashboard section.",
        sections=config.navigation_sections,
        controls=("view", "refresh", "logout"),
        data_visible=True,
    )
