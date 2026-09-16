@echo off
setlocal
cd /d "%~dp0"

echo.
echo  AI Internship Agent
 echo ==================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Could not create the virtual environment. Install Python 3.11+ first.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo.
echo Starting the dashboard...
echo Browser: http://127.0.0.1:8000/dashboard
echo Press Ctrl+C in this window to stop the agent.
echo.
start "" "http://127.0.0.1:8000/dashboard"
python -m app.main
pause
