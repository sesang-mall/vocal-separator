@echo off
rem Start the App Launcher server (localhost:8888) if needed, then open it in Edge.
set "APP_DIR=D:\Claude_Dev\app-launcher"
set "URL=http://localhost:8888/"

call :listening
if not errorlevel 1 goto open

cd /d "%APP_DIR%" || (echo Folder not found: %APP_DIR% & pause & exit /b 1)
rem Use python (not pythonw): pythonw has no stderr, so the HTTP server fails to log and drops every response.
powershell -NoProfile -Command "Start-Process python -ArgumentList 'server.py' -WorkingDirectory '%APP_DIR%' -WindowStyle Hidden"

set /a TRIES=0
:wait
set /a TRIES+=1
if %TRIES% gtr 30 (echo Server did not start on port 8888. Run "python server.py" in %APP_DIR% to see the error. & pause & exit /b 1)
timeout /t 1 /nobreak >nul
call :listening
if errorlevel 1 goto wait

:open
start "" msedge "%URL%" 2>nul && exit /b 0
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" "%URL%" & exit /b 0
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" "%URL%" & exit /b 0
)
start "" "%URL%"
exit /b 0

:listening
rem errorlevel 0 = something is already listening on port 8888
netstat -ano | findstr /R /C:"127.0.0.1:8888 .*LISTENING" /C:"\[::1\]:8888 .*LISTENING" >nul
exit /b %errorlevel%
