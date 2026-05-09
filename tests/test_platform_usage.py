from datetime import date

from deepseek_monitor.platform_usage import (
    PLATFORM_USAGE_AMOUNT_URL,
    PLATFORM_USAGE_COST_URL,
    PLATFORM_USER_SUMMARY_URL,
    PlatformRateLimitError,
    fetch_platform_balance,
    fetch_platform_usage,
    parse_platform_balance,
    parse_platform_usage,
)


def test_parse_platform_usage_sums_token_types_and_requests():
    amount_payload = {
        "total": [],
        "days": [
            {
                "date": "2026-05-01",
                "data": [
                    {
                        "model": "deepseek-chat",
                        "usage": [
                            {"type": "REQUEST", "amount": "3"},
                            {"type": "RESPONSE_TOKEN", "amount": "100"},
                            {"type": "PROMPT_CACHE_MISS_TOKEN", "amount": "40"},
                            {"type": "PROMPT_CACHE_HIT_TOKEN", "amount": "10"},
                        ],
                    }
                ],
            },
            {
                "date": "2026-05-02",
                "data": [
                    {
                        "model": "deepseek-reasoner",
                        "usage": [
                            {"type": "REQUEST", "amount": "2"},
                            {"type": "RESPONSE_TOKEN", "amount": "80"},
                            {"type": "PROMPT_CACHE_MISS_TOKEN", "amount": "20"},
                        ],
                    }
                ],
            },
        ],
    }
    cost_payload = [
        {
            "currency": "CNY",
            "total": [],
            "days": [
                {
                    "date": "2026-05-01",
                    "data": [
                        {
                            "model": "deepseek-chat",
                            "usage": [
                                {"type": "RESPONSE_TOKEN", "amount": "0.12"},
                                {"type": "PROMPT_CACHE_MISS_TOKEN", "amount": "0.08"},
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    summary = parse_platform_usage(amount_payload, cost_payload)

    assert summary.total_tokens == 250
    assert summary.total_requests == 5
    assert summary.total_cost == 0.2
    assert summary.by_day[date(2026, 5, 1)].tokens == 150
    assert summary.by_day[date(2026, 5, 1)].cost == 0.2
    assert summary.by_model["deepseek-chat"].requests == 3
    assert summary.by_model["deepseek-reasoner"].tokens == 100


def test_fetch_platform_usage_uses_platform_token_and_month_query():
    calls = []

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, headers, params, timeout):
        calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        if url == PLATFORM_USAGE_AMOUNT_URL:
            return Response({"data": {"biz_data": {"total": [], "days": []}}})
        return Response({"data": {"biz_data": []}})

    summary = fetch_platform_usage("platform-token", 2026, 5, http_get=fake_get, timeout=3)

    assert summary.total_tokens == 0
    assert calls == [
        {
            "url": PLATFORM_USAGE_AMOUNT_URL,
            "headers": {"Authorization": "Bearer platform-token", "X-App-Version": "20240425.0"},
            "params": {"year": 2026, "month": 5},
            "timeout": 3,
        },
        {
            "url": PLATFORM_USAGE_COST_URL,
            "headers": {"Authorization": "Bearer platform-token", "X-App-Version": "20240425.0"},
            "params": {"year": 2026, "month": 5},
            "timeout": 3,
        },
    ]


def test_parse_platform_balance_sums_cny_wallets():
    payload = {
        "normal_wallets": [
            {"currency": "CNY", "balance": "100.50"},
            {"currency": "USD", "balance": "9.00"},
        ],
        "bonus_wallets": [
            {"currency": "CNY", "balance": "5.25"},
        ],
    }

    balance = parse_platform_balance(payload)

    assert balance.is_available is True
    assert balance.currency == "CNY"
    assert balance.total == 105.75


def test_fetch_platform_balance_uses_platform_token():
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": {
                    "biz_data": {
                        "normal_wallets": [{"currency": "CNY", "balance": "100.50"}],
                        "bonus_wallets": [{"currency": "CNY", "balance": "5.25"}],
                    }
                }
            }

    def fake_get(url, headers, timeout):
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        return Response()

    balance = fetch_platform_balance("platform-token", http_get=fake_get, timeout=3)

    assert balance.total == 105.75
    assert calls == [
        {
            "url": PLATFORM_USER_SUMMARY_URL,
            "headers": {"Authorization": "Bearer platform-token", "X-App-Version": "20240425.0"},
            "timeout": 3,
        }
    ]


def test_fetch_platform_balance_rejects_platform_error_payload():
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"code": 40002, "msg": "Missing Token", "data": None}

    try:
        fetch_platform_balance("bad-token", http_get=lambda *args, **kwargs: Response())
    except ValueError as exc:
        assert "Missing Token" in str(exc)
    else:
        raise AssertionError("expected platform error payload to raise")


def test_fetch_platform_balance_reports_rate_limit_cleanly():
    class Response:
        status_code = 429
        headers = {"Retry-After": "120"}

        def raise_for_status(self):
            import requests

            raise requests.HTTPError("429 Client Error", response=self)

        def json(self):
            return {}

    try:
        fetch_platform_balance("rate-limited", http_get=lambda *args, **kwargs: Response())
    except PlatformRateLimitError as exc:
        assert "120 秒" in str(exc)
    else:
        raise AssertionError("expected rate limit error")
