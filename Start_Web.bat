@echo off
cd /d "%~dp0"
echo Installing dependencies...
pip install flask -q
echo.
echo Starting Screenshot Organizer on http://localhost:5000
echo Press Ctrl+C to stop.
echo.
timeout /t 2 /nobreak >nul
start "" http://localhost:5000
python app.py
pause
