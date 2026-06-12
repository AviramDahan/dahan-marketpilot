"""Pure helpers for rendering the Phase 1 dashboard safety shell."""

from __future__ import annotations

from dashboard.models import DashboardSafetyState, default_safety_state


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
