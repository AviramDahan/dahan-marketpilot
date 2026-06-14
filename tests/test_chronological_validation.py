from marketpilot.backtest_reports import WindowStatus, build_validation_windows
from marketpilot.validation import ValidationStatus, run_chronological_validation


def test_chronological_validation_passes_when_all_windows_available():
    result = run_chronological_validation(build_validation_windows(2020, 2022, 2021))

    assert result.status is ValidationStatus.PASSED
    assert result.reasons == ()


def test_chronological_validation_marks_unavailable_windows():
    result = run_chronological_validation(build_validation_windows(2022, 2022, 2022))

    assert result.status is ValidationStatus.UNAVAILABLE
    assert "window_unavailable:out_of_sample" in result.reasons
    assert any(window.status is WindowStatus.UNAVAILABLE for window in result.windows)
