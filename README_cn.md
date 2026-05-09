中文 | **[English](README.md)**

# DeepSeek Monitor

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=fff)
![PySide6](https://img.shields.io/badge/PySide6-6.x-4FC08D?style=flat-square&logo=qt&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

一个 Windows 桌面小工具，只通过 DeepSeek 官方余额接口查询账户余额。

## 跑起来

```bash
pip install PySide6 requests
python main.py
```

用 Conda 的话：

```bash
conda run -n py11-tools python main.py
```

打开 **设置**，填写 DeepSeek API Key，再点 **刷新余额**。

## 怎么用

- 使用官方余额接口：`https://api.deepseek.com/user/balance`
- API Key 保存在 `%APPDATA%/DeepSeekMonitor/config.json`
- 未配置 API Key 时余额显示 `¥0.00`
- 保留 Windows 通知、自动刷新余额、开机启动和安装版卸载功能

## 文件结构

```
main.py                      # 入口
deepseek_monitor/
  app.py                     # PySide6 界面
  deepseek_api.py            # DeepSeek 官方余额 API
  desktop_integration.py     # 开机启动、通知文案、卸载辅助
  storage.py                 # %APPDATA% 下的配置读写
tests/
  test_balance.py            # 余额响应解析测试
  test_desktop_integration.py
  test_storage.py
```

## 打包成 exe

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller pytest
.\.venv\Scripts\python.exe -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

产物在 `dist/DeepSeekMonitor.exe`。

## 安装包

安装包使用 Inno Setup 6 构建。先打包 exe，再运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

安装时可以选择安装目录，也可以选择是否开机启动。卸载时会删除安装器安装的程序文件，并清理 `%APPDATA%\DeepSeekMonitor`。

## 许可协议

MIT
