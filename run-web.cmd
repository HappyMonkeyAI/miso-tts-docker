@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
    echo Copy .env.example to .env and set HF_TOKEN before running.
    exit /b 1
)

docker compose up -d --build miso-api web
if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%

echo.
echo Miso web demo starting...
echo   Web UI:  http://localhost:%WEB_PORT%
echo   Miso API http://localhost:%MISO_API_PORT%
echo.
echo First launch loads MisoTTS on GPU and Whisper on CPU — allow a few minutes.
echo Open http://localhost:8000 in your browser (or your WEB_PORT if customized).
endlocal