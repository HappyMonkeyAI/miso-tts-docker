# Build the MisoTTS Docker image.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

docker compose build
Write-Host "Build complete. Run .\run-demo.ps1 to test." -ForegroundColor Green