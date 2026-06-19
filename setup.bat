@echo off
echo.
echo ==========================================
echo   Vocal Separator App - Setup
echo ==========================================
echo.

echo [1/4] Checking Python version...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)
echo OK: Python found.
echo.

echo [2/4] Checking FFmpeg...
ffmpeg -version > nul 2>&1
if errorlevel 1 (
    echo WARNING: FFmpeg is not installed.
    echo Install FFmpeg:
    echo   - Chocolatey : choco install ffmpeg
    echo   - Winget     : winget install FFmpeg
    echo   - Manual     : https://ffmpeg.org/download.html
    echo.
    choice /C YN /M "Continue without FFmpeg? (Y=Yes, N=No)"
    if errorlevel 2 exit /b 1
) else (
    echo OK: FFmpeg found.
)
echo.

echo [3/4] Installing Python packages...
echo (This may take 5-10 minutes)
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Package installation failed.
    pause
    exit /b 1
)
echo OK: Packages installed.
echo.

echo [4/4] Done!
echo.
echo ==========================================
echo   Setup complete!
echo   Run the app with: python main.py
echo ==========================================
echo.
pause
