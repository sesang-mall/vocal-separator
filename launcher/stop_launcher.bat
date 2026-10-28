@echo off
rem Stop the App Launcher server (processes listening on port 8888).
set "FOUND="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"127.0.0.1:8888 .*LISTENING" /C:"\[::1\]:8888 .*LISTENING"') do (
    taskkill /f /pid %%P >nul 2>&1
    set "FOUND=1"
)
if defined FOUND (echo App Launcher server stopped.) else (echo App Launcher server is not running.)
timeout /t 2 /nobreak >nul
