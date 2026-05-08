from datetime import date

from deepseek_monitor.usage import aggregate_usage, parse_usage_csv


def test_parse_usage_csv_accepts_common_deepseek_export_columns():
    csv_text = """date,model,tokens,cost,requests
2026-05-01,deepseek-chat,1200,0.35,3
2026-05-01,deepseek-reasoner,800,0.62,1
"""

    rows = parse_usage_csv(csv_text)

    assert len(rows) == 2
    assert rows[0].day == date(2026, 5, 1)
    assert rows[0].model == "deepseek-chat"
    assert rows[0].tokens == 1200
    assert rows[0].cost == 0.35
    assert rows[0].requests == 3


def test_aggregate_usage_groups_by_day_and_model():
    csv_text = """date,model,tokens,cost,requests
2026-05-01,deepseek-chat,1200,0.35,3
2026-05-01,deepseek-reasoner,800,0.62,1
2026-05-02,deepseek-chat,500,0.18,2
"""

    summary = aggregate_usage(parse_usage_csv(csv_text))

    assert summary.total_tokens == 2500
    assert summary.total_cost == 1.15
    assert summary.total_requests == 6
    assert summary.by_day[date(2026, 5, 1)].tokens == 2000
    assert summary.by_day[date(2026, 5, 2)].cost == 0.18
    assert summary.by_model["deepseek-chat"].tokens == 1700
    assert summary.by_model["deepseek-reasoner"].requests == 1
