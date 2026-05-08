$ErrorActionPreference = "Stop"

conda run -n base pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name DeepSeekMonitor `
  main.py
