@echo off
cd /d "%~dp0"
echo ==============================================
echo   BEVERAGE LINE — FULL SYSTEM LAUNCH
echo ==============================================
echo.
echo Starting local backend + dashboard...
echo   [1] Local Backend   (engine + MQTT -> HiveMQ Cloud)
echo   [2] Local Dashboard (http://localhost:8501, remote mode via MQTT)
echo.
echo Cloud dashboard opens in your browser:
echo   https://tuma206mdi-beverage-line-cloud-dashboard.streamlit.app
echo.
echo Close each terminal window to stop that process.
echo ==============================================
echo.

start "Local Backend"   cmd /c "cd /d %~dp0 && python local_backend.py && pause"
timeout /t 2 /nobreak >nul
start "Local Dashboard" cmd /c "cd /d %~dp0 && set DASHBOARD_MODE=remote && streamlit run dashboard/app.py --server.port 8501 && pause"
timeout /t 3 /nobreak >nul
start "" "https://tuma206mdi-beverage-line-cloud-dashboard.streamlit.app"

echo All launched.
pause
