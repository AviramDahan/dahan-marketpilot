from marketpilot.backtest_reports import WindowStatus, build_validation_windows


def test_windows_include_full_yearly_in_sample_and_out_of_sample():
    windows = build_validation_windows(2020, 2022, 2021)
    by_name = {window.name: window for window in windows}

    assert by_name["full_period"].status is WindowStatus.AVAILABLE
    assert by_name["year_2020"].status is WindowStatus.AVAILABLE
    assert by_name["year_2021"].status is WindowStatus.AVAILABLE
    assert by_name["year_2022"].status is WindowStatus.AVAILABLE
    assert by_name["in_sample"].start_year == 2020
    assert by_name["out_of_sample"].start_year == 2022


def test_small_dataset_marks_out_of_sample_unavailable():
    windows = build_validation_windows(2022, 2022, 2022)
    by_name = {window.name: window for window in windows}

    assert by_name["out_of_sample"].status is WindowStatus.UNAVAILABLE
    assert by_name["out_of_sample"].reason == "insufficient_out_of_sample_history"
