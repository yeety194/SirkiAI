# Build Sirki.exe with PyInstaller (run on Windows).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean packaging/sirkiai.spec

Copy-Item .env.example dist\.env -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "Build complete: dist\Sirki.exe"
Write-Host "1) Run scripts\start_local_brain.ps1 to start Ollama + hermes3:3b"
Write-Host "2) Ensure dist\.env has BRAIN_MODE=local"
Write-Host "3) Launch dist\Sirki.exe"
