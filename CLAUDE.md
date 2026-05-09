# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DeepSeek Monitor 是一个 Windows 桌面应用，用于通过 DeepSeek 官方余额接口查询账户余额。使用 PySide6 构建 GUI，不包含平台 userToken、Token 用量、CSV 用量导入或平台私有 API 调用。

## 常用命令

```bash
# 运行应用
python main.py

# 运行测试
pytest

# 运行单个测试
pytest tests/test_balance.py::test_fetch_balance_uses_deepseek_balance_endpoint_and_bearer_auth

# 打包为 exe (Windows) — 需要先创建 .venv
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller pytest
.\.venv\Scripts\python.exe -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

## 架构

```
main.py                     # 入口，调用 deepseek_monitor.app.main()
deepseek_monitor/
  app.py                    # PySide6 GUI：MainWindow、SettingsDialog、余额卡片
  deepseek_api.py           # DeepSeek 官方余额查询 (fetch_balance, parse_balance_response)
  desktop_integration.py    # 开机启动、通知文案、卸载辅助
  storage.py                # 配置存储 (%APPDATA%/DeepSeekMonitor/)
  assets/
    app.ico                 # 应用图标（exe 和窗口标题栏）
    app.png                 # 应用图标 PNG 版本
tests/
  test_balance.py           # 余额 API 响应解析测试
  test_desktop_integration.py
  test_storage.py
```

## 数据流

1. **余额查询**：`app.py` → `deepseek_api.fetch_balance()` → DeepSeek 官方余额 API → `Balance` dataclass
2. **配置持久化**：API Key 和桌面设置保存到 `%APPDATA%/DeepSeekMonitor/config.json`

## 关键设计决策

- 只使用官方余额接口：`https://api.deepseek.com/user/balance`
- 无 API Key 时余额显示 `¥0.00`
- 余额刷新在后台 `QThread` 中执行，避免网络请求阻塞 GUI
- 所有金额使用 CNY 展示
- GUI 样式内嵌在 `app.py` 的 `_apply_style()` 中，深色主题，圆角卡片设计

## 依赖

- `PySide6` - GUI 框架
- `requests` - HTTP 请求
- `pyinstaller` - 打包工具
