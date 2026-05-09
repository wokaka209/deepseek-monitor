**[中文版](README_cn.md)** | English

# DeepSeek Monitor

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=fff)
![PySide6](https://img.shields.io/badge/PySide6-6.x-4FC08D?style=flat-square&logo=qt&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A Windows desktop app for checking your DeepSeek account balance through the official balance API.

## Getting started

```bash
pip install PySide6 requests
python main.py
```

Or with Conda:

```bash
conda run -n py11-tools python main.py
```

Open **设置**, enter your DeepSeek API Key, then click **刷新余额**.

## How it works

- Uses the official balance endpoint: `https://api.deepseek.com/user/balance`
- Stores the API Key in `%APPDATA%/DeepSeekMonitor/config.json`
- Shows `¥0.00` when no API Key is configured
- Supports optional Windows notifications, auto refresh, startup launch, and installer uninstall

## File structure

```
main.py                      # Entry point
deepseek_monitor/
  app.py                     # PySide6 GUI
  deepseek_api.py            # Official DeepSeek balance API
  desktop_integration.py     # Startup, notification text, uninstall helpers
  storage.py                 # Config under %APPDATA%
tests/
  test_balance.py            # Balance response parsing
  test_desktop_integration.py
  test_storage.py
```

## Building the exe

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller pytest
.\.venv\Scripts\python.exe -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

Output lands in `dist/DeepSeekMonitor.exe`.

## Installer

The installer is built with Inno Setup 6. Build the exe first, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

The installer lets users choose the install directory and optionally start the app with Windows. Uninstall removes installer-managed program files and cleans `%APPDATA%\DeepSeekMonitor`.

## License

MIT
