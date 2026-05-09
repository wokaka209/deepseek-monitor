from deepseek_monitor.app import usage_summary_from_saved_csv


def test_empty_saved_usage_displays_zero_instead_of_sample_data():
    summary = usage_summary_from_saved_csv("")

    assert summary.total_tokens == 0
    assert summary.total_cost == 0
    assert summary.total_requests == 0
    assert summary.by_day == {}
    assert summary.by_model == {}

