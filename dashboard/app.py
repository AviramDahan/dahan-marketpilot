"""Thin Streamlit composition layer for the read-only dashboard shell."""

from datetime import datetime, timezone

from dashboard.auth import AuthStatus, DashboardAuth, authenticate_dashboard
from dashboard.data import load_dashboard_snapshot
from dashboard.pages import PAGE_REGISTRY, render_page
from dashboard.config import load_dashboard_config
from dashboard.safety_view import build_dashboard_shell


def maybe_enable_auto_refresh(st: object, *, seconds: int) -> None:
    """Enable controlled dashboard refresh when Streamlit exposes the helper."""

    if seconds <= 0:
        return
    fragment = getattr(st, "fragment", None)
    if fragment is None:
        return

    @fragment(run_every=f"{seconds}s")
    def _refresh_tick() -> None:
        st.caption("Auto-refresh active")

    _refresh_tick()


def render_page_view(st: object, view: object) -> None:
    """Render a typed page view while preserving read-only display semantics."""

    st.subheader(view.title)
    banner = getattr(view, "freshness_banner", None)
    level = getattr(view, "freshness_level", None)
    rendered_banner = False

    if banner:
        if level == "fresh":
            st.success(banner)
        elif level == "stale":
            st.warning(banner)
        elif level == "error":
            st.error(banner)
        else:
            st.info(banner)
        rendered_banner = True

    for line in view.lines:
        if rendered_banner and line == banner:
            continue
        st.write(line)


def resolve_dashboard_auth(st: object, config: object) -> DashboardAuth:
    """Resolve dashboard authentication through an explicit login action."""

    if st.session_state["dashboard_authenticated"]:
        return DashboardAuth(status=AuthStatus.AUTHENTICATED, authenticated=True)

    password = st.text_input("Dashboard password", type="password")
    login_clicked = st.button("Login", disabled=not bool(password))
    auth = authenticate_dashboard(config, password) if login_clicked else DashboardAuth.from_config(config)
    if auth.authenticated:
        st.session_state["dashboard_authenticated"] = True
    return auth


def main() -> None:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install Streamlit to run the local dashboard shell.") from exc

    config = load_dashboard_config()
    st.set_page_config(page_title="Dahan MarketPilot", layout="wide")

    if "dashboard_authenticated" not in st.session_state:
        st.session_state["dashboard_authenticated"] = False

    auth = resolve_dashboard_auth(st, config)

    shell = build_dashboard_shell(config=config, auth=auth)
    st.title(shell.title)
    st.warning(shell.disclaimer)
    st.caption(shell.paper_only_status)
    st.caption(shell.read_only_status)
    st.info(shell.status)

    if not shell.data_visible:
        return

    maybe_enable_auto_refresh(st, seconds=config.gentle_poll_seconds)
    snapshot = load_dashboard_snapshot(config, now=datetime.now(timezone.utc))
    selected = st.tabs([page.title for page in PAGE_REGISTRY])
    for tab, page in zip(selected, PAGE_REGISTRY):
        with tab:
            view = render_page(page.slug, snapshot)
            render_page_view(st, view)

    if st.button("Refresh"):
        st.rerun()
    if st.button("Logout"):
        st.session_state["dashboard_authenticated"] = False
        st.rerun()


if __name__ == "__main__":
    main()
