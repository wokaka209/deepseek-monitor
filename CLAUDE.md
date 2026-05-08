# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DeepSeek Monitor 是一个 Windows 桌面应用，用于监控 DeepSeek API 用量和账户余额。使用 PySide6 构建 GUI，支持导入 CSV 用量数据和实时查询余额。

## 常用命令

```bash
# 运行应用
python main.py

# 运行测试
pytest

# 运行单个测试
pytest tests/test_usage.py::test_parse_usage_csv_accepts_common_deepseek_export_columns

# 打包为 exe (Windows)
powershell -File build_exe.ps1
```

## 架构

```
main.py                     # 入口，调用 deepseek_monitor.app.main()
deepseek_monitor/
  app.py                    # PySide6 GUI：MainWindow、MetricCard、ModelRow、TokenChart
  deepseek_api.py           # DeepSeek API 余额查询 (fetch_balance, parse_balance_response)
  storage.py                # 配置存储 (%APPDATA%/DeepSeekMonitor/)，CSV 读写
  usage.py                  # 用量数据模型：UsageRow、UsageMetric、UsageSummary，CSV 解析
tests/
  test_balance.py           # 余额 API 响应解析测试
  test_usage.py             # CSV 解析和聚合逻辑测试
```

## 数据流

1. **余额查询**：`app.py` → `deepseek_api.fetch_balance()` → DeepSeek API → `Balance` dataclass
2. **CSV 导入**：用户选择文件 → `usage.parse_usage_csv()` → `usage.aggregate_usage()` → `UsageSummary` → `storage.save_usage_csv()`
3. **配置持久化**：API Key 保存到 `%APPDATA%/DeepSeekMonitor/config.json`

## 关键设计决策

- CSV 解析器使用 `_pick()` 函数支持多种列名格式（如 `date`/`day`/`time`/`created_at`），兼容 DeepSeek 不同版本的导出格式
- 无 API Key 时显示示例余额（¥25.75）和示例用量数据
- 所有金额使用 CNY 货币单位
- GUI 样式内嵌在 `app.py` 的 `_apply_style()` 中，深色主题，圆角卡片设计

## 依赖

- `PySide6` - GUI 框架
- `requests` - HTTP 请求
- `pyinstaller` - 打包工具
