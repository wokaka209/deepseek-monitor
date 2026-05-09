from __future__ import annotations

import subprocess
import sys
from math import ceil
from pathlib import Path
from typing import Optional, Tuple

from .storage import APP_DIR


APP_NAME = "DeepSeek Monitor"


def build_startup_command(exe_path: Path) -> str:
    return f'"{exe_path}" --minimized'


def find_uninstaller(app_dir: Path) -> Optional[Path]:
    candidate = app_dir / "unins000.exe"
    if candidate.exists():
        return candidate
    return None


def format_refresh_notification(balance_total: float) -> Tuple[str, str]:
    return (
        "DeepSeek Monitor 已更新",
        f"余额：¥{balance_total:.2f}",
    )


def remaining_cooldown_seconds(last_started: float, now: float, cooldown_seconds: int) -> int:
    if last_started <= 0:
        return 0
    return max(0, ceil(cooldown_seconds - (now - last_started)))


def set_startup_enabled(enabled: bool, exe_path: Optional[Path] = None) -> None:
    if sys.platform != "win32":
        return
    import winreg

    path = exe_path or Path(sys.executable)
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, build_startup_command(path))
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def launch_uninstaller(app_dir: Path) -> bool:
    uninstaller = find_uninstaller(app_dir)
    if uninstaller is None:
        return False
    subprocess.Popen([str(uninstaller)])
    return True


def installed_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def config_dir() -> Path:
    return APP_DIR
