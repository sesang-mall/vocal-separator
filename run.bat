@echo off
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    pause
    exit /b 1
)
where pythonw >nul 2>&1
if errorlevel 1 (
    python main.py
    if errorlevel 1 pause
) else (
    start "" pythonw main.py
)
