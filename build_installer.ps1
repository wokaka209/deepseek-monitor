$ErrorActionPreference = "Stop"

$SetupScript = Join-Path $PSScriptRoot "installer\DeepSeekMonitor.iss"
$Exe = Join-Path $PSScriptRoot "dist\DeepSeekMonitor.exe"
$Candidates = @(
  "iscc",
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
  "C:\Program Files\Inno Setup 6\ISCC.exe"
)

if (-not (Test-Path -LiteralPath $Exe)) {
  throw "Missing dist\DeepSeekMonitor.exe. Run .\build_exe.ps1 first."
}

$Iscc = $null
foreach ($Candidate in $Candidates) {
  $Command = Get-Command $Candidate -ErrorAction SilentlyContinue
  if ($Command) {
    $Iscc = $Command.Source
    break
  }
}

if (-not $Iscc) {
  throw "Inno Setup 6 compiler was not found. Install Inno Setup 6, then run this script again."
}

& $Iscc $SetupScript
