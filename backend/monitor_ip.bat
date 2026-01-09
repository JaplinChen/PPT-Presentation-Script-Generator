@echo off
setlocal

:: Determine log file path
set "LOG_DIR=%~dp0logs"
set "IP=%1"

if "%IP%"=="" (
    set /p "IP=Enter IP to monitor (e.g. 192.168.1.50): "
)

:: Replace colons with underscores for filename safety (e.g. ipv6 or port suffix if any)
set "SAFE_IP=%IP::=_%"
set "LOG_FILE=%LOG_DIR%\%SAFE_IP%.log"

if not exist "%LOG_FILE%" (
    echo Log file not found for %IP%: %LOG_FILE%
    echo Waiting for activity...
)

echo Monitoring %IP%...
start "Monitor: %IP%" powershell -NoExit -Command "Get-Content '%LOG_FILE%' -Wait -Tail 10 -Encoding UTF8"
