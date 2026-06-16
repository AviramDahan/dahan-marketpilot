from datetime import datetime, timezone

from marketpilot.scheduler_calendar import (
    MarketSessionStatus,
    MarketSkipReason,
    evaluate_market_session,
    is_nyse_early_close,
    nyse_holiday_name,
)


def test_market_session_is_open_in_summer_dst_window():
    decision = evaluate_market_session(now=datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc))

    assert decision.eligible_for_orders is True
    assert decision.status is MarketSessionStatus.OPEN
    assert decision.observed_at_et.hour == 10
    assert decision.observed_at_et.utcoffset().total_seconds() == -4 * 3600


def test_market_session_is_open_in_winter_est_window():
    decision = evaluate_market_session(now=datetime(2026, 1, 5, 15, 0, tzinfo=timezone.utc))

    assert decision.eligible_for_orders is True
    assert decision.observed_at_et.hour == 10
    assert decision.observed_at_et.utcoffset().total_seconds() == -5 * 3600


def test_weekend_is_closed():
    decision = evaluate_market_session(now=datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc))

    assert decision.eligible_for_orders is False
    assert decision.status is MarketSessionStatus.CLOSED
    assert decision.reason is MarketSkipReason.WEEKEND


def test_holiday_is_closed():
    assert nyse_holiday_name(datetime(2026, 6, 19, tzinfo=timezone.utc).date()) == "juneteenth"

    decision = evaluate_market_session(now=datetime(2026, 6, 19, 15, 0, tzinfo=timezone.utc))

    assert decision.eligible_for_orders is False
    assert decision.reason is MarketSkipReason.HOLIDAY
    assert decision.holiday_name == "juneteenth"


def test_early_close_day_uses_one_pm_et_close():
    day_after_thanksgiving = datetime(2026, 11, 27, 17, 30, tzinfo=timezone.utc)

    assert is_nyse_early_close(day_after_thanksgiving.date()) is True
    decision = evaluate_market_session(now=day_after_thanksgiving)

    assert decision.eligible_for_orders is True
    assert decision.early_close is True
    assert decision.session_close_et.hour == 13


def test_stale_scheduled_cycle_skips_order_creation():
    decision = evaluate_market_session(
        now=datetime(2026, 6, 16, 15, 30, tzinfo=timezone.utc),
        scheduled_for=datetime(2026, 6, 16, 15, 0, tzinfo=timezone.utc),
        stale_after_seconds=600,
    )

    assert decision.eligible_for_orders is False
    assert decision.status is MarketSessionStatus.STALE
    assert decision.reason is MarketSkipReason.STALE_SCHEDULED_CYCLE
    assert decision.age_seconds == 1800


def test_naive_datetime_is_rejected():
    try:
        evaluate_market_session(now=datetime(2026, 6, 16, 14, 0))
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError("naive datetime should be rejected")

