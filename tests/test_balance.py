from deepseek_monitor.deepseek_api import BALANCE_URL, fetch_balance, parse_balance_response


def test_parse_balance_response_uses_available_balance_for_cny():
    payload = {
        "is_available": True,
        "balance_infos": [
            {
                "currency": "CNY",
                "total_balance": "25.75",
                "granted_balance": "0.00",
                "topped_up_balance": "25.75",
            }
        ],
    }

    balance = parse_balance_response(payload)

    assert balance.is_available is True
    assert balance.currency == "CNY"
    assert balance.total == 25.75


def test_fetch_balance_uses_deepseek_balance_endpoint_and_bearer_auth():
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "is_available": True,
                "balance_infos": [{"currency": "CNY", "total_balance": "110.00"}],
            }

    def fake_get(url, headers, timeout):
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        return Response()

    balance = fetch_balance("sk-test", http_get=fake_get, timeout=3)

    assert balance.total == 110.0
    assert calls == [
        {
            "url": BALANCE_URL,
            "headers": {"Authorization": "Bearer sk-test"},
            "timeout": 3,
        }
    ]
