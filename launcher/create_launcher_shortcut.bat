@echo off
rem Create "App Launcher" and "App Launcher Stop" shortcuts on the desktop.
set "HERE=%~dp0"
powershell -NoProfile -Command ^
  "$d=[Environment]::GetFolderPath('Desktop'); $w=New-Object -ComObject WScript.Shell;" ^
  "$s=$w.CreateShortcut($d+'\App Launcher.lnk');$s.TargetPath='%HERE%launcher.bat';$s.WorkingDirectory='%HERE%';$s.IconLocation='%HERE%launcher_icon.ico';$s.WindowStyle=7;$s.Save();" ^
  "$s=$w.CreateShortcut($d+'\App Launcher Stop.lnk');$s.TargetPath='%HERE%stop_launcher.bat';$s.WorkingDirectory='%HERE%';$s.IconLocation='%HERE%launcher_stop_icon.ico';$s.WindowStyle=7;$s.Save()"
echo Desktop shortcuts created.
pause
