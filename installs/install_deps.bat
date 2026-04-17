@echo off
echo Installing required dependencies...
py -m pip install redis loguru fastapi uvicorn schedule
echo.
echo Installation complete!
pause
