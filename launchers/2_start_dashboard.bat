@echo off
cd /d "%~dp0"
cd ..
echo =====================================
echo   LOCAL DASHBOARD — SCHEMATIC/TRENDS/ALARMS
echo   http://localhost:8501
echo =====================================
echo.
set DASHBOARD_MODE=remote
streamlit run dashboard/app.py --server.port 8501
pause
