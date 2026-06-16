from dashboard.app import render_page_view
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
