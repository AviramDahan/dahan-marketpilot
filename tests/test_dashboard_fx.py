from datetime import datetime, timedelta, timezone
from decimal import Decimal

from dashboard.fx_view import FxDisplayStatus, render_usd_nis


NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)


def test_fx_display_renders_usd_and_fresh_nis_metadata():
    display = render_usd_nis(
        Decimal("100.00"),
        fx_rate=Decimal("3.70"),
        fx_source="Bank of Israel",
        fx_timestamp=NOW - timedelta(hours=1),
        now=NOW,
    )

    assert display.status is FxDisplayStatus.AVAILABLE
    assert display.usd_text == "USD 100.00"
    assert display.nis_text == "NIS 370.00"
    assert display.fx_source == "Bank of Israel"
    assert display.fx_timestamp == NOW - timedelta(hours=1)


def test_missing_fx_preserves_usd_and_marks_nis_unavailable():
    display = render_usd_nis(
        Decimal("100.00"),
        fx_rate=None,
        fx_source=None,
        fx_timestamp=None,
        now=NOW,
    )

    assert display.status is FxDisplayStatus.UNAVAILABLE
    assert display.usd_text == "USD 100.00"
    assert display.nis_text == "NIS unavailable"
    assert display.reason == "missing_fx_metadata"


def test_stale_fx_preserves_usd_and_marks_nis_stale():
    display = render_usd_nis(
        Decimal("100.00"),
        fx_rate=Decimal("3.70"),
        fx_source="Bank of Israel",
        fx_timestamp=NOW - timedelta(hours=30),
        now=NOW,
        stale_after_seconds=86400,
    )

    assert display.status is FxDisplayStatus.STALE
    assert display.usd_text == "USD 100.00"
    assert display.nis_text == "NIS stale"
    assert display.reason == "stale_fx_metadata"
