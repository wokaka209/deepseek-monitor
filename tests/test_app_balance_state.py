from deepseek_monitor.app import balance_api_state
from deepseek_monitor.deepseek_api import Balance


def test_balance_api_state_is_red_without_api_key():
    subtitle, color = balance_api_state("", Balance(False, "CNY", 0.0))

    assert subtitle == "未使用 API"
    assert color == "#ff5c5c"


def test_balance_api_state_is_green_with_api_key():
    subtitle, color = balance_api_state("sk-test", Balance(True, "CNY", 25.75))

    assert subtitle == "账户可用"
    assert color == "#49e86f"
