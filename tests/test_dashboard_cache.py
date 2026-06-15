from datetime import datetime, timedelta, timezone

from dashboard.cache import (
    CacheFreshnessLevel,
    DashboardCacheConfig,
    classify_cache_freshness,
    handle_source_read_failure,
    manual_refresh_actions,
)


NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)


def test_cache_freshness_thresholds_are_explicit():
    config = DashboardCacheConfig(cache_ttl_seconds=60, stale_warning_seconds=600, stale_error_seconds=1800)

    assert classify_cache_freshness(NOW - timedelta(seconds=59), now=NOW, config=config) is CacheFreshnessLevel.FRESH
    assert classify_cache_freshness(NOW - timedelta(seconds=600), now=NOW, config=config) is CacheFreshnessLevel.STALE_WARNING
    assert classify_cache_freshness(NOW - timedelta(seconds=1800), now=NOW, config=config) is CacheFreshnessLevel.STALE_ERROR


def test_manual_refresh_is_read_only_observability():
    actions = manual_refresh_actions()

    assert actions == ("clear_display_cache", "retry_read")
    assert "submit" not in " ".join(actions)
    assert "send" not in " ".join(actions)
    assert "upload" not in " ".join(actions)


def test_failed_read_with_last_good_cache_is_fail_visible():
    result = handle_source_read_failure(
        last_good={"source": "quantconnect"},
        source_timestamp=NOW - timedelta(minutes=45),
        cache_timestamp=NOW - timedelta(minutes=35),
        now=NOW,
        error_message="api token secret-value failed",
    )

    assert result.has_last_good is True
    assert result.freshness is CacheFreshnessLevel.STALE_ERROR
    assert result.source_timestamp == NOW - timedelta(minutes=45)
    assert result.cache_timestamp == NOW - timedelta(minutes=35)
    assert "secret-value" not in result.safe_error
    assert "[redacted]" in result.safe_error


def test_failed_read_without_cache_is_not_available():
    result = handle_source_read_failure(
        last_good=None,
        source_timestamp=None,
        cache_timestamp=None,
        now=NOW,
        error_message="QuantConnect unavailable",
    )

    assert result.has_last_good is False
    assert result.freshness is CacheFreshnessLevel.NOT_AVAILABLE
    assert result.safe_error == "QuantConnect unavailable"
