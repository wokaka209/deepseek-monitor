from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import requests

from .deepseek_api import Balance
from .usage import UsageRow, UsageSummary, aggregate_usage


PLATFORM_APP_VERSION = "20240425.0"
PLATFORM_USER_SUMMARY_URL = "https://platform.deepseek.com/api/v0/users/get_user_summary"
PLATFORM_USAGE_AMOUNT_URL = "https://platform.deepseek.com/api/v0/usage/amount"
PLATFORM_USAGE_COST_URL = "https://platform.deepseek.com/api/v0/usage/cost"
TOKEN_USAGE_TYPES = (
    "RESPONSE_TOKEN",
    "PROMPT_CACHE_MISS_TOKEN",
    "PROMPT_CACHE_HIT_TOKEN",
)


class PlatformRateLimitError(RuntimeError):
    pass


def fetch_platform_balance(
    platform_token: str,
    timeout: float = 30.0,
    http_get: Callable[..., Any] = requests.get,
) -> Balance:
    response = http_get(
        PLATFORM_USER_SUMMARY_URL,
        headers=_platform_headers(platform_token),
        timeout=timeout,
    )
    _raise_for_status(response)
    return parse_platform_balance(_extract_biz_data(_checked_platform_payload(response.json())))


def fetch_platform_usage(
    platform_token: str,
    year: int,
    month: int,
    timeout: float = 30.0,
    http_get: Callable[..., Any] = requests.get,
) -> UsageSummary:
    headers = _platform_headers(platform_token)
    params = {"year": year, "month": month}

    amount_response = http_get(PLATFORM_USAGE_AMOUNT_URL, headers=headers, params=params, timeout=timeout)
    _raise_for_status(amount_response)
    cost_response = http_get(PLATFORM_USAGE_COST_URL, headers=headers, params=params, timeout=timeout)
    _raise_for_status(cost_response)

    return parse_platform_usage(
        _extract_biz_data(_checked_platform_payload(amount_response.json())),
        _extract_biz_data(_checked_platform_payload(cost_response.json())),
    )


def parse_platform_balance(summary_data: Dict[str, Any]) -> Balance:
    wallets = list(summary_data.get("normal_wallets") or []) + list(summary_data.get("bonus_wallets") or [])
    cny_total = round(
        sum(_parse_float(item.get("balance")) for item in wallets if str(item.get("currency", "")).upper() == "CNY"),
        6,
    )
    if cny_total:
        return Balance(True, "CNY", cny_total)
    for item in wallets:
        currency = str(item.get("currency") or "CNY")
        return Balance(True, currency, _parse_float(item.get("balance")))
    return Balance(False, "CNY", 0.0)


def parse_platform_usage(amount_data: Dict[str, Any], cost_data: Optional[Any] = None) -> UsageSummary:
    rows: Dict[Tuple[date, str], UsageRow] = {}

    for day, model, usage in _iter_daily_usage(amount_data):
        rows[(day, model)] = UsageRow(
            day=day,
            model=model,
            tokens=sum(_usage_amount(usage, usage_type) for usage_type in TOKEN_USAGE_TYPES),
            cost=0.0,
            requests=_usage_amount(usage, "REQUEST"),
        )

    costs = _daily_costs(cost_data)
    for key, cost in costs.items():
        current = rows.get(key)
        if current is None:
            rows[key] = UsageRow(day=key[0], model=key[1], tokens=0, cost=cost, requests=0)
        else:
            rows[key] = UsageRow(
                day=current.day,
                model=current.model,
                tokens=current.tokens,
                cost=cost,
                requests=current.requests,
            )

    return aggregate_usage(row for row in rows.values() if row.tokens or row.cost or row.requests)


def _platform_headers(platform_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_normalize_platform_token(platform_token)}",
        "X-App-Version": PLATFORM_APP_VERSION,
    }


def _normalize_platform_token(platform_token: str) -> str:
    token = platform_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token.strip("\"'")


def _raise_for_status(response: Any) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code == 429:
            retry_after = _retry_after_seconds(getattr(exc.response, "headers", {}) or {})
            if retry_after:
                raise PlatformRateLimitError(f"DeepSeek 平台接口限流，请等待 {retry_after} 秒后再刷新。") from exc
            raise PlatformRateLimitError("DeepSeek 平台接口限流，请稍后再刷新。") from exc
        raise


def _retry_after_seconds(headers: Dict[str, str]) -> int:
    value = headers.get("Retry-After") or headers.get("retry-after")
    if not value:
        return 0
    try:
        return max(0, int(float(value)))
    except ValueError:
        return 0


def _checked_platform_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    code = payload.get("code", 0)
    if code not in (0, None):
        raise ValueError(str(payload.get("msg") or f"Platform API error: {code}"))
    data = payload.get("data")
    if isinstance(data, dict):
        biz_code = data.get("biz_code", 0)
        if biz_code not in (0, None):
            raise ValueError(str(data.get("biz_msg") or f"Platform business error: {biz_code}"))
    return payload


def _extract_biz_data(payload: Dict[str, Any]) -> Any:
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "biz_data" in data:
        return data["biz_data"]
    return data or {}


def _iter_daily_usage(data: Dict[str, Any]) -> Iterable[Tuple[date, str, List[Dict[str, Any]]]]:
    for raw_day in data.get("days") or []:
        day = _parse_day(str(raw_day.get("date") or ""))
        for raw_model in raw_day.get("data") or []:
            yield day, str(raw_model.get("model") or "unknown"), raw_model.get("usage") or []


def _daily_costs(cost_data: Optional[Any]) -> Dict[Tuple[date, str], float]:
    costs: Dict[Tuple[date, str], float] = {}
    for bucket in _cost_buckets(cost_data):
        for day, model, usage in _iter_daily_usage(bucket):
            key = (day, model)
            costs[key] = round(costs.get(key, 0.0) + _sum_usage_amounts(usage), 6)
    return costs


def _cost_buckets(cost_data: Optional[Any]) -> Iterable[Dict[str, Any]]:
    if isinstance(cost_data, list):
        return [item for item in cost_data if isinstance(item, dict)]
    if isinstance(cost_data, dict):
        return [cost_data]
    return []


def _usage_amount(usage: List[Dict[str, Any]], usage_type: str) -> int:
    for item in usage:
        if item.get("type") == usage_type:
            return _parse_int(item.get("amount"))
    return 0


def _sum_usage_amounts(usage: List[Dict[str, Any]]) -> float:
    return round(sum(_parse_float(item.get("amount")) for item in usage), 6)


def _parse_day(value: str) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _parse_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value).replace(",", "").strip()))


def _parse_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return round(float(str(value).replace(",", "").strip()), 6)
