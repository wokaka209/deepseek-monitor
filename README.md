**[中文版](README_cn.md)** | English

# DeepSeek Monitor

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=fff)
![PySide6](https://img.shields.io/badge/PySide6-6.x-4FC08D?style=flat-square&logo=qt&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A small tool for checking DeepSeek account balance. Windows desktop app, dark theme, double-click to run.

## Table of Contents

- [What is this](#what-is-this)
- [Getting started](#getting-started)
- [How it works](#how-it-works)
- [File structure](#file-structure)
- [Build](#build)
- [Built with](#built-with)
- [License](#license)

## What is this

A Windows desktop app that calls the official DeepSeek balance API to check your account balance. That's it, nothing else.

Supports: Windows notifications for balance changes, auto-start on boot, Inno Setup installer.

## Getting started

```bash
pip install PySide6 requests
python main.py
```

With Conda:

```bash
conda run -n py11-tools python main.py
```

Open **Settings**, enter your API Key, then click **Refresh Balance**.

## How it works

Calls `https://api.deepseek.com/user/balance` with Bearer Token auth, displays the balance on a card.

- API Key stored in `%APPDATA%/DeepSeekMonitor/config.json`
- Shows `¥0.00` when no Key is configured
- Refresh runs in a background thread, doesn't block the UI

## File structure

```
main.py                      # Entry point
deepseek_monitor/
  app.py                     # PySide6 GUI, all UI code lives here
  deepseek_api.py            # Balance API call and response parsing
  desktop_integration.py     # Auto-start, notifications, uninstall
  storage.py                 # Config read/write
  assets/
    app.ico                  # App icon
    app.png
tests/
  test_balance.py            # Balance response parsing
  test_desktop_integration.py
  test_storage.py
```

## Build

Build exe:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller pytest
.\.venv\Scripts\python.exe -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

Build installer (requires exe built first):

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

Installer lets you choose install directory and auto-start option. Uninstall cleans up `%APPDATA%\DeepSeekMonitor`.

## Built with

- **PySide6** — Qt for Python, for the GUI
- **requests** — calls DeepSeek API
- **PyInstaller** — packages into exe
- **Inno Setup 6** — builds the installer

## License

MIT
