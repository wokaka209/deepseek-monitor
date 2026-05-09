from pathlib import Path

from deepseek_monitor.desktop_integration import (
    build_startup_command,
    find_uninstaller,
    format_refresh_notification,
    remaining_cooldown_seconds,
)
from deepseek_monitor.storage import AppConfig


def test_app_config_defaults_enable_notifications_and_auto_refresh():
    config = AppConfig()

    assert config.notifications_enabled is True
    assert config.auto_refresh_enabled is True
    assert config.refresh_interval_minutes == 30
    assert config.startup_enabled is False


def test_build_startup_command_runs_exe_minimized():
    command = build_startup_command(Path(r"C:\Program Files\DeepSeek Monitor\DeepSeekMonitor.exe"))

    assert command == r'"C:\Program Files\DeepSeek Monitor\DeepSeekMonitor.exe" --minimized'


def test_find_uninstaller_only_returns_installer_generated_file(tmp_path):
    app_dir = tmp_path / "DeepSeekMonitor"
    app_dir.mkdir()
    assert find_uninstaller(app_dir) is None

    uninstaller = app_dir / "unins000.exe"
    uninstaller.write_bytes(b"exe")

    assert find_uninstaller(app_dir) == uninstaller


def test_format_refresh_notification_includes_balance():
    title, body = format_refresh_notification(105.725939)

    assert title == "DeepSeek Monitor 已更新"
    assert body == "余额：¥105.73"


def test_remaining_cooldown_seconds_rounds_up():
    assert remaining_cooldown_seconds(last_started=100.0, now=130.1, cooldown_seconds=300) == 270
    assert remaining_cooldown_seconds(last_started=100.0, now=401.0, cooldown_seconds=300) == 0
