@echo off
echo ========================================
echo Force Restart Monitoring Service
echo ========================================
echo.

echo Stopping old monitoring process...
for /f "tokens=2" %%i in ('type pids\monitoring.pid 2^>nul') do (
    echo Killing PID: %%i
    taskkill /F /PID %%i >nul 2>&1
)

echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul

echo Starting new monitoring service...
start /B venv\Scripts\python.exe monitoring\healthcheck.py > logs\monitoring.log.out 2> logs\monitoring.log.err

echo Waiting for startup...
timeout /t 3 /nobreak >nul

echo.
echo Checking if monitoring is running...
curl -s http://localhost:8000/health/live >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Monitoring started successfully!
    echo.
    echo Testing health endpoint...
    curl -s http://localhost:8000/health
) else (
    echo ✗ Monitoring failed to start
    echo.
    echo Check logs:
    type logs\monitoring.log.err
)

echo.
pause
