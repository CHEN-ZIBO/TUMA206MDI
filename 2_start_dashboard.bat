@echo off
cd /d "%~dp0"
echo =====================================
echo   LOCAL DASHBOARD — SCHEMATIC/TRENDS/ALARMS
echo   http://localhost:8501
echo =====================================
echo.
streamlit run dashboard/app.py --server.port 8501
pause
