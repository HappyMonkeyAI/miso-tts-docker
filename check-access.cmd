@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
    echo Copy .env.example to .env and set HF_TOKEN before running.
    exit /b 1
)

docker compose run --rm demo python /app/scripts/preflight.py
endlocal