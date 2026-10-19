@echo off
rem Allows only this PowerShell process to run the bundled installer.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1"
if errorlevel 1 (
 echo Installation did not finish. Keep this message and ask your agent for help.
 pause
 exit /b 1
)
echo Installation completed. You can close this window.
pause
