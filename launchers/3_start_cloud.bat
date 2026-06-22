@echo off
cd /d "%~dp0"
cd ..
echo =====================================
echo   CLOUD MONITOR — read-only MQTT
echo   http://localhost:8502
echo =====================================
echo.
set DASHBOARD_MODE=remote
streamlit run cloud_app.py --server.port 8502
pause
