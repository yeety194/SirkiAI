# Build SirkiAI with PyInstaller (run on Windows).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm packaging/sirkiai.spec

Write-Host "Build complete: dist/SirkiAI/SirkiAI.exe"
Write-Host "Copy .env.example to dist/SirkiAI/.env and configure Hermes credentials."
