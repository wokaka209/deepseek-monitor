**[中文版](README_cn.md)** | English

# DeepSeek Monitor

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=fff)
![PySide6](https://img.shields.io/badge/PySide6-6.x-4FC08D?style=flat-square&logo=qt&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

A Windows desktop app that keeps an eye on your DeepSeek API spending. Shows balance, usage trends, and per-model breakdown — all in one dark-themed dashboard.

## Table of Contents

- [What is this](#what-is-this)
- [Getting started](#getting-started)
- [How it works](#how-it-works)
- [File structure](#file-structure)
- [Building the exe](#building-the-exe)
- [Built with](#built-with)
- [License](#license)

## What is this

DeepSeek Monitor talks to the DeepSeek API to fetch your account balance. You can also import the usage CSV exported from the DeepSeek platform — it parses tokens, costs, and request counts, then charts everything by day and model.

No API key? No problem. The app falls back to sample data so you can see what the dashboard looks like before connecting.

## Getting started

```bash
pip install PySide6 requests
python main.py
```

Or if you're using Conda:

```bash
conda run -n py11-tools python main.py
```

The app window opens. Click **设置** to enter your API key, then **刷新余额** to pull live data.

## How it works

Three modes:

1. **No API key** — shows sample balance (¥25.75) and fake usage data. Good for previewing the UI.
2. **API key set** — click "刷新余额" to hit the DeepSeek balance endpoint. Real numbers replace the placeholders.
3. **CSV import** — click "导入 Usage CSV", pick the file exported from DeepSeek. The app aggregates everything and redraws the charts.

Your API key gets saved to `%APPDATA%/DeepSeekMonitor/config.json`. CSV data goes to `%APPDATA%/DeepSeekMonitor/usage.csv`.

## File structure

```
main.py                      # Entry point
deepseek_monitor/
  app.py                     # All the GUI stuff — windows, cards, charts
  deepseek_api.py            # Fetches balance from DeepSeek
  storage.py                 # Reads/writes config and CSV to %APPDATA%
  usage.py                   # Parses CSV, aggregates by day and model
tests/
  test_balance.py            # Balance response parsing
  test_usage.py              # CSV parsing and aggregation
```

The CSV parser handles multiple column name variants (`date`/`day`/`time`/`created_at`, etc.) so it works with different DeepSeek export formats.

## Building the exe

```powershell
conda run -n py11-tools python -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

Output lands in `dist/DeepSeekMonitor.exe`. Uses the `py11-tools` Conda environment and PyInstaller with `--onefile --windowed`.

## Built with

- **PySide6** — Qt for Python, the GUI framework
- **requests** — HTTP client for the DeepSeek API
- **PyInstaller** — packages everything into a single .exe

## License

MIT
