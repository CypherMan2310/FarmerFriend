@echo off
rem Farmer Advisory Assistant - double-click to start.
rem First run: creates .venv, installs packages, downloads models and documents, builds the
rem index (about 20-30 minutes). Later runs start the app in about 30 seconds.
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

if not exist ".venv\Scripts\python.exe" (
    echo [setup] Creating the Python 3.12 environment...
    py -3.12 -m venv .venv || goto :error
    echo [setup] Installing packages...
    ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt || goto :error
)

if not exist "data\index\chroma" (
    echo [setup] Downloading models and documents and building the index...
    ".venv\Scripts\python.exe" scripts\build_data.py || goto :error
)

echo Starting Farmer Advisory Assistant. Your browser opens when it is ready.
echo Close this window to stop the app.
".venv\Scripts\python.exe" -m src.app.gradio_app --open
if errorlevel 1 goto :error
goto :eof

:error
echo.
echo Something went wrong. Read the messages above.
pause
exit /b 1
