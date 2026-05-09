from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "DeepSeekMonitor"
CONFIG_FILE = APP_DIR / "config.json"


@dataclass
class AppConfig:
    api_key: str = ""
    notifications_enabled: bool = True
    auto_refresh_enabled: bool = True
    refresh_interval_minutes: int = 30
    startup_enabled: bool = False


def load_config() -> AppConfig:
    if not CONFIG_FILE.exists():
        return AppConfig()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppConfig()
    return AppConfig(
        api_key=str(data.get("api_key", "")),
        notifications_enabled=bool(data.get("notifications_enabled", True)),
        auto_refresh_enabled=bool(data.get("auto_refresh_enabled", True)),
        refresh_interval_minutes=_parse_refresh_interval(data.get("refresh_interval_minutes", 30)),
        startup_enabled=bool(data.get("startup_enabled", False)),
    )


def save_config(config: AppConfig) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(
            {
                "api_key": config.api_key,
                "notifications_enabled": config.notifications_enabled,
                "auto_refresh_enabled": config.auto_refresh_enabled,
                "refresh_interval_minutes": config.refresh_interval_minutes,
                "startup_enabled": config.startup_enabled,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _parse_refresh_interval(value: object) -> int:
    try:
        return max(5, int(value or 30))
    except (TypeError, ValueError):
        return 30
