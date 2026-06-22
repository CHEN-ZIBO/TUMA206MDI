@echo off
cd /d "%~dp0"
echo ==============================================
echo   BEVERAGE LINE — FULL SYSTEM LAUNCH
echo ==============================================
echo.
echo Starting 3 windows...
echo   [1] Local Backend    (engine + MQTT)
echo   [2] Local Dashboard  (http://localhost:8501)
echo   [3] Cloud Monitor    (http://localhost:8502)
echo.
echo Close each window to stop that process.
echo ==============================================
echo.

start "Local Backend"    cmd /c "cd /d %~dp0 && python local_backend.py && pause"
start "Local Dashboard"  cmd /c "cd /d %~dp0 && streamlit run dashboard/app.py --server.port 8501 && pause"
start "Cloud Monitor"    cmd /c "cd /d %~dp0 && set DASHBOARD_MODE=remote && streamlit run cloud_app.py --server.port 8502 && pause"

echo All three launched.
pause
