from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import requests


BALANCE_URL = "https://api.deepseek.com/user/balance"


@dataclass(frozen=True)
class Balance:
    is_available: bool
    currency: str
    total: float


def parse_balance_response(payload: Dict[str, Any]) -> Balance:
    infos = payload.get("balance_infos") or []
    preferred = None
    for item in infos:
        if str(item.get("currency", "")).upper() == "CNY":
            preferred = item
            break
    if preferred is None and infos:
        preferred = infos[0]
    if preferred is None:
        return Balance(bool(payload.get("is_available")), "CNY", 0.0)

    return Balance(
        is_available=bool(payload.get("is_available")),
        currency=str(preferred.get("currency") or "CNY"),
        total=float(preferred.get("total_balance") or 0),
    )


def fetch_balance(api_key: str, timeout: float = 10.0) -> Balance:
    response = requests.get(
        BALANCE_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return parse_balance_response(response.json())
