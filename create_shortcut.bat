@echo off
rem 바탕화면에 아이콘이 적용된 "Vocal Separator" 바로가기를 만듭니다.
set "APP=%~dp0"
powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Vocal Separator.lnk');" ^
  "$s.TargetPath='%APP%run.bat';$s.WorkingDirectory='%APP%';" ^
  "$s.IconLocation='%APP%assets\icon.ico';$s.WindowStyle=7;$s.Save()"
echo Desktop shortcut created.
pause
