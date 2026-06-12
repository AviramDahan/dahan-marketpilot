from math import inf, nan

from marketpilot.data_quality import (
    DataQualityIssue,
    DataQualityStatus,
    UniverseCandidate,
    UniverseDecision,
    has_finite_number,
    unique_issues,
)


def test_data_quality_issue_codes_are_sanitized():
    assert DataQualityIssue.CRITICAL_MISSING_DATA.value == "critical_missing_data"
    assert "secret" not in DataQualityIssue.CRITICAL_MISSING_DATA.value
    assert "token" not in DataQualityIssue.UNSUPPORTED_SECURITY.value


def test_universe_candidate_normalizes_symbol():
    candidate = UniverseCandidate(
        symbol=" msft ",
        price=350,
        history_bars=300,
        average_volume_20=1000000,
        average_dollar_volume_20=350000000,
    )

    assert candidate.normalized_symbol() == "MSFT"


def test_universe_decision_acceptance_status():
    accepted = UniverseDecision("MSFT", DataQualityStatus.ACCEPTED)
    rejected = UniverseDecision("XYZ", DataQualityStatus.REJECTED, (DataQualityIssue.BELOW_MIN_PRICE,))

    assert accepted.accepted is True
    assert rejected.accepted is False


def test_finite_numeric_guard_rejects_nan_and_infinity():
    assert has_finite_number(10.0) is True
    assert has_finite_number(nan) is False
    assert has_finite_number(inf) is False
    assert has_finite_number(None) is False


def test_unique_issues_preserves_order():
    issues = unique_issues(
        [
            DataQualityIssue.STALE_DATA,
            DataQualityIssue.STALE_DATA,
            DataQualityIssue.BELOW_MIN_PRICE,
        ]
    )

    assert issues == (DataQualityIssue.STALE_DATA, DataQualityIssue.BELOW_MIN_PRICE)

