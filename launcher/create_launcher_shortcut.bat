@echo off
rem Create an "App Launcher" shortcut on the desktop.
set "HERE=%~dp0"
powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\App Launcher.lnk');" ^
  "$s.TargetPath='%HERE%launcher.bat';$s.WorkingDirectory='%HERE%';" ^
  "$s.IconLocation='%HERE%launcher_icon.ico';$s.WindowStyle=7;$s.Save()"
echo Desktop shortcut created.
pause
