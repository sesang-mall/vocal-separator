@echo off
rem Start the App Launcher server (localhost:8888) if needed, then open it in Chrome.
set "APP_DIR=D:\Claude_Dev\app-launcher"
set "URL=http://localhost:8888/"

curl -s -o nul %URL%
if not errorlevel 1 goto open

cd /d "%APP_DIR%" || (echo Folder not found: %APP_DIR% & pause & exit /b 1)
where pythonw >nul 2>&1
if errorlevel 1 (start "" /min python server.py) else (start "" pythonw server.py)

set /a TRIES=0
:wait
set /a TRIES+=1
if %TRIES% gtr 30 (echo Server did not start on port 8888. & pause & exit /b 1)
timeout /t 1 /nobreak >nul
curl -s -o nul %URL%
if errorlevel 1 goto wait

:open
start "" chrome "%URL%" 2>nul && exit /b 0
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%URL%" & exit /b 0
)
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "%URL%" & exit /b 0
)
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" "%URL%" & exit /b 0
)
start "" "%URL%"
