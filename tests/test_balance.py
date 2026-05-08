from deepseek_monitor.deepseek_api import parse_balance_response


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
