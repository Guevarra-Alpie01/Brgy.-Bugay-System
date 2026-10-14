@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Error: the project virtual environment was not found at "%~dp0.venv".
    exit /b 1
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Error: failed to activate the project virtual environment.
    exit /b 1
)

python manage.py runserver
