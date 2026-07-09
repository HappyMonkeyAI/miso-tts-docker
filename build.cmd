@echo off
setlocal
cd /d "%~dp0"

docker compose build misotts
if %ERRORLEVEL% EQU 0 echo Build complete. Run run-demo.cmd to test.
endlocal