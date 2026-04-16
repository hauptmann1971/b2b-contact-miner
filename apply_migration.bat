@echo off
echo Applying database migration for task_queue table...
echo.

venv\Scripts\python.exe migrations\apply_migrations.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Migration completed successfully!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Update main.py to use DatabaseTaskQueue
    echo 2. Run: .\start_all.ps1 restart
    echo.
) else (
    echo.
    echo ========================================
    echo Migration FAILED!
    echo ========================================
    echo Please check the error message above.
    echo.
)

pause
