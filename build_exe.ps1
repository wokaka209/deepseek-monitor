$ErrorActionPreference = "Stop"

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
  throw "Missing local virtual environment. Run: py -3.12 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller pytest"
}

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --icon ".\deepseek_monitor\assets\app.ico" `
  --add-data ".\deepseek_monitor\assets\app.ico;deepseek_monitor\assets" `
  --add-binary "C:\Users\coolkey\AppData\Local\Programs\Python\Python312\python3.dll;." `
  --add-binary ".\.venv\Lib\site-packages\PySide6\Qt6Core.dll;." `
  --add-binary ".\.venv\Lib\site-packages\PySide6\pyside6.abi3.dll;." `
  --add-binary ".\.venv\Lib\site-packages\shiboken6\shiboken6.abi3.dll;." `
  --add-binary ".\.venv\Lib\site-packages\PySide6\msvcp140.dll;." `
  --add-binary ".\.venv\Lib\site-packages\PySide6\msvcp140_1.dll;." `
  --add-binary ".\.venv\Lib\site-packages\PySide6\vcruntime140.dll;." `
  --add-binary ".\.venv\Lib\site-packages\PySide6\vcruntime140_1.dll;." `
  --add-binary "C:\Windows\System32\icu.dll;." `
  --add-binary "C:\Windows\System32\icuin.dll;." `
  --add-binary "C:\Windows\System32\icuuc.dll;." `
  --name DeepSeekMonitor `
  main.py
