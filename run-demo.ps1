# Run the built-in multi-turn conversation demo.
# First run downloads ~30-40 GB of model weights into the Docker volume.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "Copy .env.example to .env and set HF_TOKEN before running." -ForegroundColor Yellow
    exit 1
}

docker compose run --rm demo