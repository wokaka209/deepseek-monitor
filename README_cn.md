中文 | **[English](README.md)**

# DeepSeek Monitor

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=fff)
![PySide6](https://img.shields.io/badge/PySide6-6.x-4FC08D?style=flat-square&logo=qt&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

一个 Windows 桌面小工具，盯着你的 DeepSeek API 花费。余额、用量趋势、各模型占比，全塞在一个深色面板里。

## 目录

- [这是什么](#这是什么)
- [跑起来](#跑起来)
- [怎么用](#怎么用)
- [文件结构](#文件结构)
- [打包成 exe](#打包成-exe)
- [用到的东西](#用到的东西)
- [许可协议](#许可协议)

## 这是什么

DeepSeek Monitor 调 DeepSeek 的接口查余额。你也可以导入从 DeepSeek 平台导出的用量 CSV —— 它会解析 token 数、费用、请求次数，然后按天、按模型画出来。

没设 API Key？没关系，应用会显示示例数据，让你先看看界面长什么样。

## 跑起来

```bash
pip install PySide6 requests
python main.py
```

用 Conda 的话：

```bash
conda run -n py11-tools python main.py
```

窗口打开后，点 **设置** 填 API Key，再点 **刷新余额** 拉真实数据。

## 怎么用

三种模式：

1. **没 API Key** —— 显示示例余额（¥25.75）和假数据，纯预览。
2. **填了 API Key** —— 点"刷新余额"调 DeepSeek 接口，真实数字替换占位符。
3. **导入 CSV** —— 点"导入 Usage CSV"，选从 DeepSeek 下载的文件，面板自动刷新。

API Key 存在 `%APPDATA%/DeepSeekMonitor/config.json`，CSV 数据存在 `%APPDATA%/DeepSeekMonitor/usage.csv`。

## 文件结构

```
main.py                      # 入口
deepseek_monitor/
  app.py                     # 所有 GUI 东西 —— 窗口、卡片、图表
  deepseek_api.py            # 调 DeepSeek 查余额
  storage.py                 # 读写配置和 CSV，存在 %APPDATA%
  usage.py                   # 解析 CSV，按天、按模型聚合
tests/
  test_balance.py            # 余额响应解析测试
  test_usage.py              # CSV 解析和聚合测试
```

CSV 解析器兼容多种列名格式（`date`/`day`/`time`/`created_at` 等），DeepSeek 不同版本导出的文件都能认。

## 打包成 exe

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller pytest
.\.venv\Scripts\python.exe -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

产物在 `dist/DeepSeekMonitor.exe`，用本地 `.venv` 打包，不依赖 Conda 在 PATH 里。

## 安装、通知和卸载

安装包使用 Inno Setup 6 构建。先打包 exe，再运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

安装时可以选择安装目录，也可以选择是否开机启动并最小化到托盘。程序默认启用 Windows 托盘通知；启动后会自动刷新一次余额和用量，之后按设置的间隔刷新。卸载时会删除安装器安装的程序文件，并清理 `%APPDATA%\DeepSeekMonitor` 配置目录。

## 用到的东西

- **PySide6** —— Qt 的 Python 绑定，做界面用
- **requests** —— HTTP 库，调 DeepSeek 接口
- **PyInstaller** —— 打包成 exe

## 许可协议

MIT
