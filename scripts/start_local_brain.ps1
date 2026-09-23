# Start a local Hermes brain via Ollama for SirkiAI (Windows).
$ErrorActionPreference = "Stop"
$Model = if ($env:LOCAL_BRAIN_MODEL) { $env:LOCAL_BRAIN_MODEL } else { "hermes3:3b" }

function Test-Ollama {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama not found. Install from https://ollama.com/download/windows then re-run this script."
    Start-Process "https://ollama.com/download/windows"
    exit 1
}

if (-not (Test-Ollama)) {
    Write-Host "Starting Ollama..."
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

Write-Host "Pulling model: $Model"
ollama pull $Model

Write-Host "Warming model..."
ollama run $Model "Reply with: SirkiAI local brain ready." | Out-Null

Write-Host ""
Write-Host "Local brain is up:"
Write-Host "  URL:   http://127.0.0.1:11434/v1"
Write-Host "  Model: $Model"
Write-Host "Set BRAIN_MODE=local in .env (or next to Sirki.exe) and launch Sirki."
