# Open an interactive shell inside the MisoTTS container.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "Copy .env.example to .env and set HF_TOKEN before running." -ForegroundColor Yellow
    exit 1
}

docker compose run --rm shell