@echo off
setlocal
cd /d "%~dp0"
title Smart Waste Collection - Setup and Run

echo ======================================================
echo  Smart Waste Collection - Windows setup
 echo ======================================================
echo.
echo Project folder: %CD%
echo Checking the default Python installation...
python --version
if errorlevel 1 goto no_python

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating a local virtual environment...
    python -m venv .venv
    if errorlevel 1 goto setup_failed
)

".venv\Scripts\python.exe" -c "import streamlit, pandas, plotly, pydeck, requests" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing required packages from requirements.txt...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto setup_failed
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_failed
)

echo.
echo Starting the dashboard in your browser...
echo To stop the app, return to this window and press Ctrl+C.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto run_failed
goto end

:no_python
echo ERROR: Python was not found by the Windows command 'python'.
echo Install Python 3.13 or 3.14, then reopen this file.
goto pause_end

:setup_failed
echo.
echo ERROR: Setup or package installation failed.
echo Check your internet connection and read the error above.
echo Your requirements.txt is located in this same folder.
goto pause_end

:run_failed
echo.
echo ERROR: The app stopped. Read the error message above.
goto pause_end

:pause_end
pause
:end
endlocal
