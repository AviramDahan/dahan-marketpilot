from dashboard.app import maybe_enable_auto_refresh, render_page_view
from dashboard.models import DashboardSectionStatus
from dashboard.pages import PageView


class FakeStreamlit:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def subheader(self, value: str) -> None:
        self.calls.append(("subheader", value))

    def success(self, value: str) -> None:
        self.calls.append(("success", value))

    def warning(self, value: str) -> None:
        self.calls.append(("warning", value))

    def error(self, value: str) -> None:
        self.calls.append(("error", value))

    def info(self, value: str) -> None:
        self.calls.append(("info", value))

    def write(self, value: str) -> None:
        self.calls.append(("write", value))

    def caption(self, value: str) -> None:
        self.calls.append(("caption", value))


class FakeRefreshStreamlit(FakeStreamlit):
    def fragment(self, *, run_every: str):
        self.calls.append(("fragment", run_every))

        def decorator(func):
            def wrapper():
                self.calls.append(("fragment_run", run_every))
                return func()

            return wrapper

        return decorator


def test_render_page_view_uses_color_coded_freshness_banner():
    for level, method in (
        ("fresh", "success"),
        ("stale", "warning"),
        ("error", "error"),
        ("unavailable", "info"),
    ):
        fake = FakeStreamlit()
        view = PageView(
            title="Overview",
            status=DashboardSectionStatus.AVAILABLE,
            lines=("Portfolio banner", "Remaining line"),
            freshness_banner="Portfolio banner",
            freshness_level=level,
        )

        render_page_view(fake, view)

        assert (method, "Portfolio banner") in fake.calls
        assert ("write", "Portfolio banner") not in fake.calls
        assert ("write", "Remaining line") in fake.calls


def test_auto_refresh_uses_streamlit_fragment_when_available():
    fake = FakeRefreshStreamlit()

    maybe_enable_auto_refresh(fake, seconds=120)

    assert ("fragment", "120s") in fake.calls
    assert ("caption", "Auto-refresh active") in fake.calls
