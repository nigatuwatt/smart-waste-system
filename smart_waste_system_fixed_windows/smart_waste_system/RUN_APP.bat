@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run INSTALL_AND_RUN.bat to create the environment and install packages.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
endlocal
