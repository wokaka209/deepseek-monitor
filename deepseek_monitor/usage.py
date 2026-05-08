from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from io import StringIO
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class UsageRow:
    day: date
    model: str
    tokens: int
    cost: float
    requests: int


@dataclass
class UsageMetric:
    tokens: int = 0
    cost: float = 0.0
    requests: int = 0

    def add(self, row: UsageRow) -> None:
        self.tokens += row.tokens
        self.cost = round(self.cost + row.cost, 6)
        self.requests += row.requests


@dataclass
class UsageSummary:
    total_tokens: int = 0
    total_cost: float = 0.0
    total_requests: int = 0
    by_day: Dict[date, UsageMetric] = field(default_factory=dict)
    by_model: Dict[str, UsageMetric] = field(default_factory=dict)


def parse_usage_csv(csv_text: str) -> List[UsageRow]:
    reader = csv.DictReader(StringIO(csv_text.strip()))
    if not reader.fieldnames:
        return []

    rows: List[UsageRow] = []
    for raw in reader:
        if not raw:
            continue
        rows.append(
            UsageRow(
                day=_parse_date(_pick(raw, "date", "day", "time", "created_at")),
                model=_pick(raw, "model", "model_name") or "unknown",
                tokens=_parse_int(_pick(raw, "tokens", "total_tokens", "token_usage")),
                cost=_parse_float(_pick(raw, "cost", "amount", "fee", "total_cost")),
                requests=max(1, _parse_int(_pick(raw, "requests", "request_count", "calls"))),
            )
        )
    return rows


def aggregate_usage(rows: Iterable[UsageRow]) -> UsageSummary:
    summary = UsageSummary()
    for row in rows:
        summary.total_tokens += row.tokens
        summary.total_cost = round(summary.total_cost + row.cost, 6)
        summary.total_requests += row.requests

        summary.by_day.setdefault(row.day, UsageMetric()).add(row)
        summary.by_model.setdefault(row.model, UsageMetric()).add(row)
    return summary


def sample_usage() -> UsageSummary:
    rows = [
        UsageRow(date(2026, 5, 1), "V4 Flash", 79600, 0.12, 22),
        UsageRow(date(2026, 5, 2), "V4 Flash", 10840000, 0.71, 96),
        UsageRow(date(2026, 5, 3), "V4 Pro", 13210000, 1.09, 118),
        UsageRow(date(2026, 5, 4), "V4 Flash", 1100000, 0.25, 41),
        UsageRow(date(2026, 5, 5), "V4 Pro", 1250000, 0.32, 47),
        UsageRow(date(2026, 5, 6), "V4 Flash", 28750000, 1.33, 184),
        UsageRow(date(2026, 5, 7), "V4 Flash", 12630000, 0.35, 91),
    ]
    return aggregate_usage(rows)


def _pick(row: Dict[str, str], *names: str) -> str:
    normalized = {key.strip().lower(): value for key, value in row.items() if key}
    for name in names:
        value = normalized.get(name)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _parse_date(value: str) -> date:
    value = value.strip()
    if not value:
        return date.today()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _parse_int(value: str) -> int:
    if not value:
        return 0
    return int(float(value.replace(",", "").strip()))


def _parse_float(value: str) -> float:
    if not value:
        return 0.0
    return round(float(value.replace(",", "").strip()), 6)
