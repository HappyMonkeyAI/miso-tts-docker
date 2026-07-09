@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: run-generate.cmd "Your text here" [output.wav]
    exit /b 1
)

if not exist ".env" (
    echo Copy .env.example to .env and set HF_TOKEN before running.
    exit /b 1
)

set "TEXT=%~1"
if "%~2"=="" (
    set "OUTPUT=generated.wav"
) else (
    set "OUTPUT=%~2"
)

docker compose run --rm generate generate --text "%TEXT%" --output "/app/output/%OUTPUT%"
if %ERRORLEVEL% EQU 0 echo Output: %~dp0output\%OUTPUT%
endlocal