@echo off
echo Installing missing dependencies...
py -m pip install deep-translator
echo.
echo Done! Now restart services with: .\start_all.ps1 restart
pause
