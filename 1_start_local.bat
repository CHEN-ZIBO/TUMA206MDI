@echo off
cd /d "%~dp0"
echo =====================================
echo   LOCAL BACKEND — engine + MQTT
echo =====================================
echo.
python local_backend.py
pause
