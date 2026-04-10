@echo off
REM =============================================================================
REM B2B Contact Miner - Full Application Startup Script (Windows)
REM =============================================================================
REM This script starts all necessary components:
REM 1. Redis (if using Docker)
REM 2. MySQL (if using Docker)
REM 3. FastAPI Monitoring Server (port 8000)
REM 4. Flask Web Server (port 5000)
REM 5. Task Scheduler (daily pipeline runs)
REM =============================================================================

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_DIR=%~dp0
set LOG_DIR=%PROJECT_DIR%logs
set PID_DIR=%PROJECT_DIR%pids

REM Create necessary directories
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%PID_DIR%" mkdir "%PID_DIR%"

echo ========================================
echo   B2B Contact Miner - Starting All Services
echo ========================================
echo.

REM Parse command line arguments
set ACTION=%1
if "%ACTION%"=="" set ACTION=start

if "%ACTION%"=="start" goto :start
if "%ACTION%"=="stop" goto :stop
if "%ACTION%"=="restart" goto :restart
if "%ACTION%"=="status" goto :status
if "%ACTION%"=="logs" goto :logs
if "%ACTION%"=="clean" goto :clean

echo Usage: %0 {start^|stop^|restart^|status^|logs [service]^|clean}
echo.
echo Commands:
echo   start   - Start all services
echo   stop    - Stop all services
echo   restart - Restart all services
echo   status  - Show service status
echo   logs    - Tail all logs (or specify service name)
echo   clean   - Remove PID files and old logs
exit /b 1

:start
echo Starting all services...
echo.

REM Step 1: Check Docker services
echo [1/6] Checking Docker services...
where docker-compose >nul 2>&1
if %errorlevel% equ 0 (
    if exist "%PROJECT_DIR%doc\docker-compose.yml" (
        echo Starting Redis and MySQL with Docker...
        cd "%PROJECT_DIR%doc"
        docker-compose up -d 2>nul
        if %errorlevel% neq 0 echo Docker services might already be running
        cd "%PROJECT_DIR%"
        timeout /t 3 /nobreak >nul
    )
) else (
    echo Docker Compose not found, skipping Docker services
)
echo.

REM Step 2: Start FastAPI Monitoring Server
echo [2/6] Starting FastAPI Monitoring Server (port 8000)...
call :start_service "monitoring" "py monitoring/healthcheck.py"
timeout /t 2 /nobreak >nul
echo.

REM Step 3: Start Flask Web Server
echo [3/6] Starting Flask Web Server (port 5000)...
call :start_service "web_server" "py web_server.py"
timeout /t 2 /nobreak >nul
echo.

REM Step 4: Start Task Scheduler
echo [4/6] Starting Task Scheduler...
call :start_service "scheduler" "py scheduler.py"
timeout /t 1 /nobreak >nul
echo.

REM Step 5: Main Pipeline info
echo [5/6] Main Pipeline ready (run 'py main.py' manually or wait for scheduler)
echo.

REM Step 6: Status check
echo [6/6] Checking service status...
echo.

call :check_service "monitoring" "8000"
call :check_service "web_server" "5000"
call :check_service "scheduler" "N/A"

echo.
echo ========================================
echo   All services started successfully!
echo ========================================
echo.
echo Access points:
echo   - Flask Web UI:      http://localhost:5000
echo   - FastAPI Health:    http://localhost:8000/health
echo   - FastAPI Docs:      http://localhost:8000/docs
echo.
echo Logs directory: %LOG_DIR%
echo PIDs directory: %PID_DIR%
echo.
echo To stop all services, run: %0 stop
goto :end

:stop
echo Stopping all services...
echo.

call :stop_service "scheduler"
call :stop_service "web_server"
call :stop_service "monitoring"

echo.
set /p STOP_DOCKER="Stop Docker containers (y/n)? "
if /i "%STOP_DOCKER%"=="y" (
    if exist "%PROJECT_DIR%doc\docker-compose.yml" (
        cd "%PROJECT_DIR%doc"
        docker-compose down 2>nul
        cd "%PROJECT_DIR%"
        echo Docker services stopped
    )
)

echo.
echo All services stopped
goto :end

:restart
echo Restarting all services...
echo.
call :stop
timeout /t 2 /nobreak >nul
echo.
call :start
goto :end

:status
echo Service Status:
echo.

call :check_service "monitoring" "8000"
call :check_service "web_server" "5000"
call :check_service "scheduler" "N/A"

echo.

REM Check Docker
where docker-compose >nul 2>&1
if %errorlevel% equ 0 (
    echo Docker Services:
    cd "%PROJECT_DIR%doc"
    docker-compose ps 2>nul
    if %errorlevel% neq 0 echo   Docker services not running
    cd "%PROJECT_DIR%"
)

echo.
echo Recent Logs:
echo.
for %%f in ("%LOG_DIR%\*.log") do (
    if exist "%%f" (
        set SERVICE_NAME=%%~nf
        echo !SERVICE_NAME!:
        powershell -Command "Get-Content '%%f' -Tail 3 | ForEach-Object { Write-Host \"  $_\" }" 2>nul
        echo.
    )
)
goto :end

:logs
set SERVICE=%2
if "%SERVICE%"=="" set SERVICE=all

if "%SERVICE%"=="all" (
    echo Tailing all logs (Ctrl+C to exit)...
    echo.
    powershell -Command "Get-ChildItem '%LOG_DIR%\*.log' | ForEach-Object { Write-Host \"=== $($_.Name) ===\"; Get-Content $_.FullName -Tail 5 -Wait }"
) else (
    set LOG_FILE=%LOG_DIR%\%SERVICE%.log
    if exist "!LOG_FILE!" (
        echo Tailing %SERVICE% logs (Ctrl+C to exit)...
        echo.
        powershell -Command "Get-Content '!LOG_FILE!' -Wait"
    ) else (
        echo Log file not found: !LOG_FILE!
        exit /b 1
    )
)
goto :end

:clean
echo Cleaning up PID files and old logs...
del /Q "%PID_DIR%\*.pid" 2>nul
forfiles /p "%LOG_DIR%" /s /m *.log /d -7 /c "cmd /c del @path" 2>nul
echo Cleanup complete
goto :end

:end
endlocal
exit /b 0

REM =============================================================================
REM Helper Functions
REM =============================================================================

:start_service
set SERVICE_NAME=%~1
set COMMAND=%~2
set LOG_FILE=%LOG_DIR%\%SERVICE_NAME%.log
set PID_FILE=%PID_DIR%\%SERVICE_NAME%.pid

if exist "%PID_FILE%" (
    set /p EXISTING_PID=<"%PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | findstr /I "python.exe" >nul
    if !errorlevel! equ 0 (
        echo %SERVICE_NAME% is already running (PID: !EXISTING_PID!)
        exit /b 0
    )
)

echo Starting %SERVICE_NAME%...
cd "%PROJECT_DIR%"
start /B cmd /C "cd /d %PROJECT_DIR% && %COMMAND%" > "%LOG_FILE%" 2>&1
timeout /t 2 /nobreak >nul

REM Get the PID of the last started process
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /R "PID:"') do (
    set LAST_PID=%%i
)

if defined LAST_PID (
    echo !LAST_PID! > "%PID_FILE%"
    echo %SERVICE_NAME% started (PID: !LAST_PID!, Log: %LOG_FILE%)
) else (
    echo %SERVICE_NAME% started (Log: %LOG_FILE%)
)
exit /b 0

:stop_service
set SERVICE_NAME=%~1
set PID_FILE=%PID_DIR%\%SERVICE_NAME%.pid

if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>nul | findstr /I "python.exe" >nul
    if !errorlevel! equ 0 (
        echo Stopping %SERVICE_NAME% (PID: !PID!)...
        taskkill /PID !PID! /F >nul 2>&1
        timeout /t 2 /nobreak >nul
        
        REM Force kill if still running
        tasklist /FI "PID eq !PID!" 2>nul | findstr /I "python.exe" >nul
        if !errorlevel! equ 0 (
            echo Force killing %SERVICE_NAME%...
            taskkill /PID !PID! /F >nul 2>&1
        )
        
        del "%PID_FILE%"
        echo %SERVICE_NAME% stopped
    ) else (
        echo %SERVICE_NAME% is not running
        del "%PID_FILE%" 2>nul
    )
) else (
    echo %SERVICE_NAME% is not running
)
exit /b 0

:check_service
set SERVICE_NAME=%~1
set PORT=%~2
set PID_FILE=%PID_DIR%\%SERVICE_NAME%.pid

if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>nul | findstr /I "python.exe" >nul
    if !errorlevel! equ 0 (
        if "%PORT%"=="N/A" (
            echo   [OK] %SERVICE_NAME% (PID: !PID!)
        ) else (
            echo   [OK] %SERVICE_NAME% (PID: !PID!, Port: %PORT%)
        )
    ) else (
        echo   [FAIL] %SERVICE_NAME% - NOT RUNNING
        del "%PID_FILE%" 2>nul
    )
) else (
    echo   [FAIL] %SERVICE_NAME% - NOT RUNNING
)
exit /b 0
