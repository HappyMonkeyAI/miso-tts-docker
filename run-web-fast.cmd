@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if not exist ".env" (
    echo Copy .env.example to .env before running.
    exit /b 1
)

call scripts\gen-dev-certs.cmd
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

docker compose up -d --build pocket-api web caddy
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "if (Test-Path '.env') { (Get-Content '.env' | Where-Object { $_ -match '^\s*DEV_CERT_IP\s*=' } | Select-Object -First 1) -replace '.*=\s*','' | ForEach-Object { $_.Trim() } }"`) do set "LAN_IP=%%I"

echo.
echo Miso web demo — Fast mode (Pocket TTS on CPU)
echo   Web UI (HTTPS, mic): https://localhost:8443
if defined LAN_IP if not "!LAN_IP!"=="" echo   Web UI (LAN):        https://!LAN_IP!:8443
echo   Web UI (HTTP):       http://localhost:8000  (mic only on localhost)
echo   Pocket API:          http://localhost:8090
echo.
echo Use the HTTPS URL for microphone access (especially over LAN IP).
echo Accept the self-signed cert warning once in your browser.
echo First launch downloads the Pocket model — allow a few minutes.
echo GPU is not required in Fast mode.
endlocal