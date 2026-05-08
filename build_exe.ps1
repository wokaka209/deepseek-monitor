$ErrorActionPreference = "Stop"

conda run -n py11-tools pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --icon ".\deepseek_monitor\assets\app.ico" `
  --add-data ".\deepseek_monitor\assets\app.ico;deepseek_monitor\assets" `
  --add-binary "D:\anaconda\envs\py11-tools\msvcp140.dll;." `
  --add-binary "D:\anaconda\envs\py11-tools\msvcp140_1.dll;." `
  --add-binary "D:\anaconda\envs\py11-tools\vcruntime140.dll;." `
  --add-binary "D:\anaconda\envs\py11-tools\vcruntime140_1.dll;." `
  --name DeepSeekMonitor `
  main.py
