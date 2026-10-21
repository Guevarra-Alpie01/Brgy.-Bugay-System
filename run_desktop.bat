@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Error: install the Python requirements first. See README.md.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" desktop.py
if errorlevel 1 (
    echo.
    echo The desktop app stopped with an error. See the message above.
    pause
    exit /b 1
)
