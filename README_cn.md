中文 | **[English](README.md)**

# DeepSeek Monitor

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=fff)
![PySide6](https://img.shields.io/badge/PySide6-6.x-4FC08D?style=flat-square&logo=qt&logoColor=fff)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

查 DeepSeek 账户余额的小工具。Windows 桌面应用，深色主题，双击就跑。

## 目录

- [这是什么](#这是什么)
- [跑起来](#跑起来)
- [怎么工作的](#怎么工作的)
- [文件结构](#文件结构)
- [打包](#打包)
- [用到的东西](#用到的东西)
- [许可协议](#许可协议)

## 这是什么

一个 Windows 桌面应用，调 DeepSeek 官方余额接口查账户余额。就这一个功能，没别的。

支持：Windows 通知提醒余额变动、开机自启、Inno Setup 安装包。

## 跑起来

```bash
pip install PySide6 requests
python main.py
```

用 Conda：

```bash
conda run -n py11-tools python main.py
```

打开后点 **设置** 填 API Key，再点 **刷新余额**。

## 怎么工作的

调 `https://api.deepseek.com/user/balance`，Bearer Token 认证，返回余额显示在卡片上。

- API Key 存在 `%APPDATA%/DeepSeekMonitor/config.json`
- 没填 Key 时余额显示 `¥0.00`
- 刷新在后台线程跑，不卡界面

## 文件结构

```
main.py                      # 入口
deepseek_monitor/
  app.py                     # PySide6 界面，所有 GUI 都在这
  deepseek_api.py            # 余额 API 调用和响应解析
  desktop_integration.py     # 开机启动、通知、卸载
  storage.py                 # 配置读写
  assets/
    app.ico                  # 应用图标
    app.png
tests/
  test_balance.py            # 余额响应解析
  test_desktop_integration.py
  test_storage.py
```

## 打包

打包 exe：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller pytest
.\.venv\Scripts\python.exe -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

打包安装包（需要先完成上面的 exe 打包）：

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

安装时可选安装目录和是否开机启动。卸载会清理 `%APPDATA%\DeepSeekMonitor`。

## 用到的东西

- **PySide6** — Qt for Python，做界面
- **requests** — 调 DeepSeek 接口
- **PyInstaller** — 打包 exe
- **Inno Setup 6** — 打包安装包

## 许可协议

MIT
