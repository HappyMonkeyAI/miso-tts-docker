@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0\.."

set "FORCE=0"
if /i "%~1"=="--force" set "FORCE=1"
if /i "%~1"=="-f" set "FORCE=1"

if not exist "certs" mkdir certs

if "%FORCE%"=="0" if exist "certs\cert.pem" if exist "certs\key.pem" (
    echo Dev TLS certs already exist in certs\
    echo Set DEV_CERT_IP in .env then run: scripts\gen-dev-certs.cmd --force
    exit /b 0
)

call :read_env DEV_CERT_IP
call :read_env DEV_CERT_HOSTNAME

set "SAN=DNS:localhost,DNS:host.docker.internal,IP:127.0.0.1,IP:::1"

if defined DEV_CERT_HOSTNAME (
    set "SAN=!SAN!,DNS:!DEV_CERT_HOSTNAME!"
    echo Using hostname from .env: !DEV_CERT_HOSTNAME!
)

if defined DEV_CERT_IP (
    call :add_ips !DEV_CERT_IP!
) else (
    echo DEV_CERT_IP not set in .env — auto-detecting LAN IP...
    for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.IPAddress -notlike '172.*' } | Select-Object -First 1 -ExpandProperty IPAddress)"`) do (
        if not "%%I"=="" (
            set "SAN=!SAN!,IP:%%I"
            echo Auto-detected LAN IP: %%I
        )
    )
)

echo.
echo Generating self-signed dev certificate...
echo SAN: !SAN!

docker run --rm -v "%CD%\certs:/certs" alpine/openssl req -x509 -newkey rsa:2048 ^
    -keyout /certs/key.pem -out /certs/cert.pem -days 825 -nodes ^
    -subj "/CN=localhost" ^
    -addext "subjectAltName=!SAN!"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Could not generate certs. Is Docker running?
    exit /b 1
)

echo.
echo Created certs\cert.pem and certs\key.pem
echo   https://localhost:8443
if defined DEV_CERT_IP echo   https://!DEV_CERT_IP!:8443
echo Accept the browser security warning once per URL.
exit /b 0

:read_env
set "%~1="
if not exist ".env" exit /b 0
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /i /b /c:"%~1=" .env`) do (
    set "VAL=%%B"
    if defined VAL set "VAL=!VAL: =!"
    if defined VAL if "!VAL:~0,1!"=="""" set "VAL=!VAL:~1,-1!"
    set "%~1=!VAL!"
)
exit /b 0

:add_ips
for %%A in (%*) do (
    set "SAN=!SAN!,IP:%%~A"
    echo Adding LAN IP from .env: %%~A
)
exit /b 0