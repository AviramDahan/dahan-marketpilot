from datetime import datetime, timedelta, timezone

from marketpilot.backtesting import classify_same_bar_ambiguity, validate_no_lookahead
from marketpilot.timeframes import BarTimeframe, StrategyMode


def _t(day: int) -> datetime:
    return datetime(2026, 1, day, tzinfo=timezone.utc)


def test_completed_signal_fills_after_signal_bar():
    result = validate_no_lookahead(
        signal_time=_t(2),
        fill_time=_t(3),
        available_bar_times=[_t(1), _t(2)],
        current_bar_time=_t(3),
    )

    assert result.passed is True
    assert result.reasons == ()


def test_current_bar_is_excluded_from_signal_evidence():
    result = validate_no_lookahead(
        signal_time=_t(3),
        fill_time=_t(4),
        available_bar_times=[_t(1), _t(2), _t(3)],
        current_bar_time=_t(3),
    )

    assert result.passed is False
    assert "current_bar_excluded" in result.reasons


def test_future_available_bar_is_rejected():
    result = validate_no_lookahead(
        signal_time=_t(2),
        fill_time=_t(3),
        available_bar_times=[_t(1), _t(2), _t(3)],
    )

    assert result.passed is False
    assert "future_bar_detected" in result.reasons


def test_same_bar_entry_exit_fails_closed():
    ambiguity = classify_same_bar_ambiguity(_t(4), _t(4))

    assert ambiguity.fail_closed is True
    assert ambiguity.reason == "entry_and_exit_on_same_bar"


def test_strategy_mode_timeframe_alignment_is_enforced():
    result = validate_no_lookahead(
        signal_time=_t(2),
        fill_time=_t(3),
        available_bar_times=[_t(1), _t(2)],
        strategy_mode=StrategyMode.DAILY_ONLY,
        signal_timeframe=BarTimeframe.FOUR_HOUR,
    )

    assert result.passed is False
    assert "strategy_mode_timeframe_mismatch" in result.reasons


def test_stale_data_is_rejected():
    result = validate_no_lookahead(
        signal_time=_t(2),
        fill_time=_t(2) + timedelta(hours=1),
        available_bar_times=[_t(1), _t(2)],
        stale_data=True,
    )

    assert result.passed is False
    assert "stale_data" in result.reasons
