@echo off

echo Starting AI Alert Monitoring System...

:: START FLASK API
start /min cmd /c "python app.py"

:: START DASHBOARD SERVER
start /min cmd /c "python -m http.server 8080"

:: START AUTO MONITORING
start /min cmd /c "python smart_monitor.py"

:: WAIT A FEW SECONDS
timeout /t 3 >nul

:: OPEN DASHBOARD
start http://localhost:8080